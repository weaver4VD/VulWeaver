import json
import logging
import random

import dgl
import pytorch_lightning as pl
import torch
import torchmetrics

import torch
from torch import nn
from torch.nn import BCELoss, BCEWithLogitsLoss
import pandas as pd
import numpy as np
from deepspeed.profiling.flops_profiler.profiler import FlopsProfiler

import nni

from sklearn.metrics import classification_report, confusion_matrix

logger = logging.getLogger(__name__)

logging.getLogger("matplotlib").setLevel(logging.WARNING)


class BaseModule(pl.LightningModule):
    def __init__(
        self, undersample_node_on_loss_factor=None, test_every=False, tune_nni=False, positive_weight=None, profile=False, time=False
    ):
        super().__init__()
        self.save_hyperparameters()
        self.class_threshold = 0.5
        metrics = torchmetrics.MetricCollection(
            [
                torchmetrics.Accuracy(),
                torchmetrics.Precision(),
                torchmetrics.Recall(),
                torchmetrics.F1Score(),
            ]
        )
        self.train_metrics = metrics.clone(prefix="train_")
        self.val_metrics = metrics.clone(prefix="val_")
        if test_every:
            self.test_every_metrics = metrics.clone(prefix="test_every_")
        else:
            self.test_every_metrics = None
        self.test_metrics = metrics.clone(prefix="test_")
        self.test_metrics_positive = metrics.clone(prefix="test_1_")
        self.test_metrics_negative = metrics.clone(prefix="test_0_")
        
        self.test_pr_curve = torchmetrics.PrecisionRecallCurve()
        self.test_pr_curve_bin = torchmetrics.BinnedPrecisionRecallCurve(1)
        self.test_preds = torchmetrics.CatMetric()
        self.test_labels = torchmetrics.CatMetric()
        self.test_confmat = torchmetrics.ConfusionMatrix(num_classes=2)
        self.test_results = []
        self.val_results = []
        self.val_preds_collect = torchmetrics.CatMetric()
        self.val_labels_collect = torchmetrics.CatMetric()
        
        self.label_proportion = nn.ModuleDict({partition + "_label_proportion": torchmetrics.MeanMetric() for partition in ["train", "val", "test"]})
        self.prediction_proportion = nn.ModuleDict({partition + "_prediction_proportion": torchmetrics.MeanMetric() for partition in ["train", "val", "test"]})
        self.label_proportion_cut = nn.ModuleDict({partition + "_label_proportion_cut": torchmetrics.MeanMetric() for partition in ["train", "val", "test"]})
        self.prediction_proportion_cut = nn.ModuleDict({partition + "_prediction_proportion_cut": torchmetrics.MeanMetric() for partition in ["train", "val", "test"]})

        self.train_portion_positive = torchmetrics.MeanMetric()

        if positive_weight is not None:
            positive_weight = torch.tensor([positive_weight])
        self.loss_fn = BCEWithLogitsLoss(pos_weight=positive_weight)

        if profile:
            self.prof = FlopsProfiler(self)
    
    def freeze_graph(self):
        logger.warn("freeze_graph not implemented")

    def get_label(self, batch):
        if self.hparams.label_style == "node":
            label = batch.ndata["_VULN"]
        elif self.hparams.label_style == "graph":
            graphs = dgl.unbatch(batch, batch.batch_num_nodes())
            label = torch.stack([g.ndata["_VULN"].max() for g in graphs])
        elif self.hparams.label_style == "dataflow_solution_out":
            label = batch.ndata["_DF_OUT"]
        elif self.hparams.label_style == "dataflow_solution_in":
            label = batch.ndata["_DF_IN"]
        else:
            raise NotImplementedError(self.hparams.label_style)
        return label.float()

    def resample(self, batch, out, label):
        """Resample logits and labels to balance vuln/nonvuln classes"""
        self.log(
            "meta/train_original_label_proportion",
            torch.mean(label).float().item(),
            on_step=True,
            on_epoch=False,
            batch_size=batch.batch_size,
        )
        self.log(
            "meta/train_original_label_len",
            torch.tensor(label.shape[0]).float(),
            on_step=True,
            on_epoch=False,
            batch_size=batch.batch_size,
        )
        vuln_indices = label.nonzero().squeeze().tolist()
        num_indices_to_sample = round(
            len(vuln_indices) * self.hparams.undersample_node_on_loss_factor
        )
        nonvuln_indices = (label == 0).nonzero().squeeze().tolist()
        nonvuln_indices = random.sample(nonvuln_indices, num_indices_to_sample)
        indices = vuln_indices + nonvuln_indices
        out = out[indices]
        label = label[indices]
        self.log(
            "meta/train_resampled_label_proportion",
            torch.mean(label).item(),
            on_step=True,
            on_epoch=False,
            batch_size=batch.batch_size,
        )
        self.log(
            "meta/train_resampled_label_len",
            torch.tensor(label.shape[0]).float(),
            on_step=True,
            on_epoch=False,
            batch_size=batch.batch_size,
        )
        return out, label

    def log_loss(self, name, loss, batch):
        self.log(
            f"{name}_loss",
            loss.item(),
            on_step=True,
            on_epoch=True,
            batch_size=batch.batch_size,
        )

    def cut_nodef(self, batch, label, out, name):
        nz_idx = batch.ndata["_ABS_DATAFLOW"].nonzero()
        label = label[nz_idx]
        out = out[nz_idx]
        return label, out
    
    def log_proportions(self, label, out, cut, name):
        label_metric = self.label_proportion_cut if cut else self.label_proportion
        pred_metric = self.prediction_proportion_cut if cut else self.prediction_proportion
        label_name = name + "_label_proportion"
        if cut:
            label_name += "_cut"
        pred_name = name + "_prediction_proportion"
        if cut:
            pred_name += "_cut"
        label_metric[label_name](label.mean())
        pred_metric[pred_name]((out > 0.5).float().mean())
        self.log(label_name, label_metric[label_name], on_step=False, on_epoch=True)
        self.log(pred_name, pred_metric[pred_name], on_step=False, on_epoch=True)

    def training_step(self, batch_data, batch_idx):
        batch, extrafeats = batch_data
        label = self.get_label(batch)
        out = self.forward(batch, extrafeats)
        if self.hparams.label_style == "dataflow_solution_in":
            label, out = self.cut_nodef(batch, label, out, "train")

        if (
            self.hparams.label_style == "node"
            and self.hparams.undersample_node_on_loss_factor is not None
        ):
            out, label = self.resample(batch, out, label)
        loss = self.loss_fn(out, label)
        self.log_loss("train", loss, batch)

        out = torch.sigmoid(out)
        label = label.int()

        self.log("train_portion_positive", self.train_portion_positive((label == 1).float().mean()), on_step=True, on_epoch=True, batch_size=len(label))
        self.train_metrics.update(out, label)

        return loss

    def validation_step(self, batch_data, batch_idx, dataloader_idx=0):
        batch, extrafeats = batch_data
        label = self.get_label(batch)
        out = self.forward(batch, extrafeats)
        if self.hparams.label_style == "dataflow_solution_in":
            label, out = self.cut_nodef(batch, label, out, "val")
        loss = self.loss_fn(out, label)

        out = torch.sigmoid(out)
        label = label.int()

        self.log_loss("val", loss, batch)
        self.val_metrics.update(out, label)
        self.val_preds_collect.update(out)
        self.val_labels_collect.update(label)
        if self.hparams.label_style == "graph":
            graphs = dgl.unbatch(batch)
            probs = out.cpu().numpy()
            preds_binary = (out > 0.5).int().cpu().numpy()
            labels_np = label.cpu().numpy()
            
            for i, graph in enumerate(graphs):
                if '_graph_id' in graph.ndata and graph.num_nodes() > 0:
                    sample_id = int(graph.ndata['_graph_id'][0].item())
                elif hasattr(graph, 'graph_id'):
                    sample_id = graph.graph_id
                else:
                    sample_id = f"unknown_val_{batch_idx}_{i}"
                self.val_results.append({
                    'id': sample_id,
                    'predicted_label': int(preds_binary[i]),
                    'true_label': int(labels_np[i]),
                    'probability': float(probs[i])
                })

    def test_step(self, batch_data, batch_idx):
        print(batch_idx)
        do_profile = self.hparams.profile and batch_idx > 2
        if do_profile:
            prof = self.prof
        do_time = self.hparams.time and batch_idx > 2
        if do_profile:
            prof.start_profile()
        if do_time:
            start = torch.cuda.Event(enable_timing=True)
            end = torch.cuda.Event(enable_timing=True)

        batch, extrafeats = batch_data
        label = self.get_label(batch)
        if do_time:
            start.record()
        out = self.forward(batch, extrafeats)
        if do_time:
            end.record()
        
        profs = []
        if do_profile:
            flops = prof.get_total_flops(as_string=True)
            params = prof.get_total_params(as_string=True)
            macs = prof.get_total_macs(as_string=True)
            prof.print_model_profile(profile_step=batch_idx, output_file=f"./profile.txt")
            prof.end_profile()
            logger.info("step %d: %s flops %s params %s macs", batch_idx, flops, params, macs)
            profs.append({
                "step": batch_idx,
                "flops": flops,
                "params": params,
                "macs": macs,
                "batch_size": len(label),
            })
        if do_time:
            torch.cuda.synchronize()
            tim = start.elapsed_time(end)
            logger.info("step %d: time %f", batch_idx, tim)
            profs.append({
                "step": batch_idx,
                "batch_size": len(label),
                "runtime": tim,
            })
        if do_profile:
            filename = f"profiledata.jsonl"
        elif do_time:
            filename = f"timedata.jsonl"
        else:
            filename = None
        if filename is not None:
            with open(filename, "a") as f:
                f.write(json.dumps(profs[0]))
                f.write("\n")

        if self.hparams.label_style == "dataflow_solution_in":
            label, out = self.cut_nodef(batch, label, out, "test")
            
        if len(out.shape) == 0:
            out = out.unsqueeze(0)
        if len(label.shape) == 0:
            label = label.unsqueeze(0)

        loss = self.loss_fn(out, label)
        self.log_loss("test", loss, batch)
        
        out = torch.sigmoid(out)
        label = label.int()

        self.test_metrics.update(out, label)
        i_pos = torch.nonzero(label == 1)
        if i_pos.shape[0] > 0:
            self.test_metrics_positive.update(out[i_pos], label[i_pos])
        i_neg = torch.nonzero(label == 0)
        if i_neg.shape[0] > 0:
            self.test_metrics_negative.update(out[i_neg], label[i_neg])
        assert len(i_pos) + len(i_neg) == len(label)

        self.test_preds.update(out)
        self.test_labels.update(label)
        probs = out.cpu().numpy()
        preds_binary = (out > 0.5).int().cpu().numpy()
        labels_np = label.cpu().numpy()
        
        if self.hparams.label_style == "graph":
            graphs = dgl.unbatch(batch)
            
            for i, graph in enumerate(graphs):
                if '_graph_id' in graph.ndata and graph.num_nodes() > 0:
                    sample_id = int(graph.ndata['_graph_id'][0].item())
                elif hasattr(graph, 'graph_id'):
                    sample_id = graph.graph_id
                else:
                    sample_id = f"unknown_{batch_idx}_{i}"
                self.test_results.append({
                    'id': sample_id,
                    'predicted_label': int(preds_binary[i]),
                    'true_label': int(labels_np[i]),
                    'probability': float(probs[i])
                })
        else:
            for i in range(len(probs)):
                if hasattr(batch, 'ndata') and 'node_id' in batch.ndata:
                    sample_id = batch.ndata['node_id'][i].item() if torch.is_tensor(batch.ndata['node_id'][i]) else batch.ndata['node_id'][i]
                else:
                    sample_id = f"node_{batch_idx}_{i}"
                self.test_results.append({
                    'id': sample_id,
                    'predicted_label': int(preds_binary[i]),
                    'true_label': int(labels_np[i]),
                    'probability': float(probs[i])
                })
        
    def training_epoch_end(self, outputs):
        self.log_dict(self.train_metrics.compute(), on_step=False, on_epoch=True)
        self.train_metrics.reset()
    
    def validation_epoch_end(self, outputs):
        ld = self.val_metrics.compute()
        self.log_dict(ld, on_step=False, on_epoch=True)
        self.val_metrics.reset()
        print("intermediate result:", ld)
        if len(self.val_results) > 0:
            preds = self.val_preds_collect.compute().cpu().numpy()
            labels = self.val_labels_collect.compute().int().cpu().numpy()
            preds_binary = preds > 0.5
            cm = confusion_matrix(labels, preds_binary)
            tn, fp, fn, tp = cm.ravel()
            
            print("\n" + "="*50)
            print("VALIDATION SET - Confusion Matrix Details:")
            print("="*50)
            print(f"True Positives (TP):  {tp}")
            print(f"False Positives (FP): {fp}")
            print(f"False Negatives (FN): {fn}")
            print(f"True Negatives (TN):  {tn}")
            print("="*50)
            total = tp + fp + fn + tn
            accuracy = (tp + tn) / total if total > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            
            print("\nDerived Metrics:")
            print(f"Accuracy:    {accuracy:.4f}")
            print(f"Precision:   {precision:.4f}")
            print(f"Recall:      {recall:.4f}")
            print(f"F1-Score:    {f1:.4f}")
            print(f"Specificity: {specificity:.4f}")
            print("="*50)
            
            print("\nPrediction Statistics:")
            print(f"Total samples:      {total}")
            print(f"Predicted positive: {tp + fp} ({(tp + fp) / total * 100:.2f}%)")
            print(f"Predicted negative: {tn + fn} ({(tn + fn) / total * 100:.2f}%)")
            print(f"Actual positive:    {tp + fn} ({(tp + fn) / total * 100:.2f}%)")
            print(f"Actual negative:    {tn + fp} ({(tn + fp) / total * 100:.2f}%)")
            print("="*50 + "\n")
            logger.info("VALIDATION - TP=%d, FP=%d, FN=%d, TN=%d", tp, fp, fn, tn)
            logger.info("VALIDATION - Precision=%.4f, Recall=%.4f, F1=%.4f", precision, recall, f1)
            self.val_preds_collect.reset()
            self.val_labels_collect.reset()
            self.val_results = []
        nni.report_intermediate_result(ld["val_F1Score"].cpu().item())
    
    def test_epoch_end(self, outputs):
        self.log_dict(self.test_metrics.compute(), on_step=False, on_epoch=True)
        self.log_dict(self.test_metrics_positive.compute(), on_step=False, on_epoch=True)
        self.log_dict(self.test_metrics_negative.compute(), on_step=False, on_epoch=True)
        self.test_metrics.reset()
        self.test_metrics_positive.reset()
        self.test_metrics_negative.reset()

        preds, labels = self.test_preds.compute(), self.test_labels.compute().int()

        precision, recall, thresholds = self.test_pr_curve(preds, labels)
        pd.DataFrame({"precision": precision.tolist(), "recall": recall.tolist(), "thresholds": thresholds.tolist() + [1]}).to_csv("pr.csv")
        precision_bin, recall_bin, thresholds_bin = self.test_pr_curve_bin(preds, labels)
        pd.DataFrame({"precision": precision_bin.tolist(), "recall": recall_bin.tolist(), "thresholds": thresholds_bin.tolist() + [1]}).to_csv("pr_binned.csv")

        preds, labels = preds.cpu().numpy(), labels.cpu().numpy()
        preds = preds > 0.5

        print(preds)
        print(labels)

        def get_n_params(model):
            pp=0
            for p in list(model.parameters()):
                nn=1
                for s in list(p.size()):
                    nn = nn*s
                pp += nn
            return pp
        n_params = get_n_params(self)
        print(f"model {n_params} parameters, model architecture {self}")

        print("classification report")
        print(classification_report(labels, preds))
        print("confusion matrix")
        cm = confusion_matrix(labels, preds)
        print(cm)
        
        tn, fp, fn, tp = cm.ravel()
        print("\n" + "="*50)
        print("Confusion Matrix Details:")
        print("="*50)
        print(f"True Positives (TP):  {tp}")
        print(f"False Positives (FP): {fp}")
        print(f"False Negatives (FN): {fn}")
        print(f"True Negatives (TN):  {tn}")
        print("="*50)

        total = tp + fp + fn + tn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        print("\nDerived Metrics:")
        print(f"Accuracy:    {accuracy:.4f}")
        print(f"Precision:   {precision:.4f}")
        print(f"Recall:      {recall:.4f}")
        print(f"F1-Score:    {f1:.4f}")
        print(f"Specificity: {specificity:.4f}")
        print("="*50)
        
        print("\nPrediction Statistics:")
        print(f"Total samples:      {total}")
        print(f"Predicted positive: {tp + fp} ({(tp + fp) / total * 100:.2f}%)")
        print(f"Predicted negative: {tn + fn} ({(tn + fn) / total * 100:.2f}%)")
        print(f"Actual positive:    {tp + fn} ({(tp + fn) / total * 100:.2f}%)")
        print(f"Actual negative:    {tn + fp} ({(tn + fp) / total * 100:.2f}%)")
        print("="*50 + "\n")

        logger.info("TP=%d, FP=%d, FN=%d, TN=%d", tp, fp, fn, tn)
        logger.info("Precision=%.4f, Recall=%.4f, F1=%.4f", precision, recall, f1)
        if len(self.test_results) > 0:
            results_df = pd.DataFrame(self.test_results)
            results_df = results_df.sort_values('id')
            
            excel_filename = "./DDFA-java/storage/test_predictions.xlsx"
            results_df.to_excel(excel_filename, index=False)
            
            print(f"\n{'='*50}")
            print(f"Predictions saved to: {excel_filename}")
            print(f"Total predictions: {len(results_df)}")
            print(f"{'='*50}\n")
            
            logger.info("Saved %d predictions to %s", len(results_df), excel_filename)
            csv_filename = "./DDFA-java/storage/test_predictions.csv"
            results_df.to_csv(csv_filename, index=False)
            logger.info("Also saved predictions to %s", csv_filename)
            print("\nSample of predictions (first 10 rows):")
            print(results_df.head(10).to_string(index=False))
            print("\n")
            self._analyze_vulnerable_pairs(results_df)
            self.test_results = []
    
    def _analyze_vulnerable_pairs(self, preds_df):
        """Analyze prediction results for vulnerable pairs."""
        import os
        
        pairs_file = "./DDFA-java/storage/external/vulnerable_pairs_test.csv"
        
        if not os.path.exists(pairs_file):
            logger.warning("Pairs file not found: %s, skipping pair analysis", pairs_file)
            return
        
        try:
            pairs_df = pd.read_csv(pairs_file)
        except Exception as e:
            logger.warning("Failed to read pairs file: %s", e)
            return
        pred_dict = dict(zip(preds_df['id'], preds_df['predicted_label']))
        both_correct = 0
        both_wrong = 0
        vuln_correct_only = 0
        nonvuln_correct_only = 0
        missing_pairs = 0
        
        pair_results = []
        
        for idx, row in pairs_df.iterrows():
            vuln_idx = row['vulnerable_index']
            nonvuln_idx = row['non_vulnerable_index']
            if vuln_idx not in pred_dict or nonvuln_idx not in pred_dict:
                missing_pairs += 1
                continue
            
            vuln_pred = pred_dict[vuln_idx]
            nonvuln_pred = pred_dict[nonvuln_idx]
            vuln_correct = (vuln_pred == 1)
            nonvuln_correct = (nonvuln_pred == 0)
            
            pair_results.append({
                'pair_idx': idx,
                'filename': row['filename'],
                'method': row['method'],
                'cve_id': row['cve_id'],
                'vulnerable_index': vuln_idx,
                'non_vulnerable_index': nonvuln_idx,
                'vuln_pred': vuln_pred,
                'nonvuln_pred': nonvuln_pred,
                'vuln_correct': vuln_correct,
                'nonvuln_correct': nonvuln_correct,
                'both_correct': vuln_correct and nonvuln_correct,
                'both_wrong': (not vuln_correct) and (not nonvuln_correct)
            })
            
            if vuln_correct and nonvuln_correct:
                both_correct += 1
            elif (not vuln_correct) and (not nonvuln_correct):
                both_wrong += 1
            elif vuln_correct:
                vuln_correct_only += 1
            else:
                nonvuln_correct_only += 1
        total_valid_pairs = len(pairs_df) - missing_pairs
        
        if total_valid_pairs > 0:
            print("\n" + "=" * 60)
            print("PAIR-WISE PREDICTION ANALYSIS")
            print("=" * 60)
            print(f"Total pairs: {len(pairs_df)}")
            print(f"Valid pairs (with predictions): {total_valid_pairs}")
            print(f"Missing pairs: {missing_pairs}")
            print()
            print(f"Both correct:           {both_correct:4d} ({both_correct/total_valid_pairs*100:6.2f}%)")
            print(f"Both wrong:             {both_wrong:4d} ({both_wrong/total_valid_pairs*100:6.2f}%)")
            print(f"Only vuln correct:      {vuln_correct_only:4d} ({vuln_correct_only/total_valid_pairs*100:6.2f}%)")
            print(f"Only non-vuln correct:  {nonvuln_correct_only:4d} ({nonvuln_correct_only/total_valid_pairs*100:6.2f}%)")
            print("=" * 60 + "\n")
            
            logger.info("Pair Analysis: both_correct=%d, both_wrong=%d, vuln_only=%d, nonvuln_only=%d",
                       both_correct, both_wrong, vuln_correct_only, nonvuln_correct_only)
            if pair_results:
                pair_results_df = pd.DataFrame(pair_results)
                output_file = "./DDFA-java/storage/pair_analysis_results.csv"
                pair_results_df.to_csv(output_file, index=False)
                print(f"Pair analysis results saved to: {output_file}")
                wrong_pairs = pair_results_df[pair_results_df['both_wrong']]
                if len(wrong_pairs) > 0:
                    print(f"\nBoth-wrong pairs examples (first 5):")
                    print(wrong_pairs[['filename', 'method', 'cve_id', 'vuln_pred', 'nonvuln_pred']].head().to_string(index=False))
                    print()
        else:
            logger.warning("No valid pairs found for analysis")
