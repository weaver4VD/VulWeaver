import torch
import torch.nn as nn
import torch
from torch.autograd import Variable
import copy
from torch.nn import CrossEntropyLoss, MSELoss
from transformers.models.roberta.modeling_roberta import RobertaClassificationHead
import torch.nn.functional as F
    
    
class Model(nn.Module):   
    def __init__(self, encoder, config, tokenizer, args):
        super(Model, self).__init__()
        self.encoder = encoder
        self.config=config
        self.tokenizer=tokenizer
        self.args=args
    
        
    def forward(self, input_ids=None, labels=None, weight=None): 
        outputs=self.encoder(input_ids,attention_mask=input_ids.ne(1))[0]
        logits=outputs
        prob=torch.sigmoid(logits)
        if labels is not None:
            labels=labels.float()
            if weight == None:
                loss=torch.log(prob[:,0]+1e-10)*labels+torch.log((1-prob)[:,0]+1e-10)*(1-labels)
            else:
                loss=torch.log(prob[:,0]+1e-10)*labels*weight[1]+torch.log((1-prob)[:,0]+1e-10)*(1-labels)*weight[0]
            loss=-loss.mean()
            return loss,prob
        else:
            return prob


class Similarity(nn.Module):
    """
    Dot product or cosine similarity
    """
    def __init__(self, temp):
        super().__init__()
        self.temp = temp 
        self.cos = nn.CosineSimilarity(dim=-1)

    def forward(self, x, y):
        return self.cos(x, y) / self.temp
    
    
class ModelWithCLR(nn.Module):   
    def __init__(self, encoder,config,tokenizer,args,clr_mask,clr_temp=1.0):
        super(ModelWithCLR, self).__init__()
        self.encoder = encoder
        self.cls_head = RobertaClassificationHead(config)
        self.sim = Similarity(temp=clr_temp)
        self.clr_mask = False if not clr_mask else True
        self.config=config
        self.tokenizer=tokenizer
        self.args=args
    
        
    def forward(self, group_inputs=None,group_labels=None): 
        batch_size = group_inputs.size(0)
        group_size = group_inputs.size(1)
        dup_group_inputs = group_inputs.repeat(1, 2, 1)
        input_ids = dup_group_inputs.view((-1, group_inputs.size(-1)))
        attention_mask = input_ids.ne(1)
        
        outputs = self.encoder(input_ids,attention_mask)
        cls_output = self.cls_head(outputs[0])
        cls_output = cls_output.view((batch_size, 2, group_size, 1)).contiguous()
        cls_output = cls_output[:, 0, :, :].contiguous()
        cls_output = cls_output.view((batch_size * group_size, 1)).contiguous()
        
        clr_output = outputs.pooler_output
        clr_output = clr_output.view((batch_size, 2, group_size, self.config.hidden_size)).contiguous()
        z_1 = clr_output[:, 0, :, :]
        z_2 = clr_output[:, 1, :, :]
        cos_sim = self.sim(z_1.unsqueeze(2), z_2.unsqueeze(1))
        loss = 0
        clr_labels = torch.arange(group_size).long().to(group_inputs.device).unsqueeze(0).expand(batch_size, group_size)
        if self.clr_mask:
            clr_mask = torch.eye(group_size).to(group_inputs.device).unsqueeze(0).expand(batch_size, group_size, group_size)
            clr_mask[:, 0, :] = 1
            clr_mask[:, :, 0] = 1
            masked_cos_sim = cos_sim.masked_fill(clr_mask == 0, -1e9)
            softmax_output = F.log_softmax(masked_cos_sim, dim=2)
            clr_loss_fct = nn.NLLLoss()
            clr_loss = clr_loss_fct(softmax_output, clr_labels)
        else:
            clr_loss_fct = nn.CrossEntropyLoss()
            clr_loss = clr_loss_fct(cos_sim, clr_labels)
        labels = group_labels.view(-1)
        logits=cls_output
        prob=torch.sigmoid(logits)
        labels=labels.float()
        cls_loss=torch.log(prob[:,0]+1e-10)*labels+torch.log((1-prob)[:,0]+1e-10)*(1-labels)
        cls_loss=-cls_loss.mean()

        loss = clr_loss + cls_loss
        
        return loss,prob,labels
 
class ModelWithCLRForClassification(ModelWithCLR):   
    def __init__(self, encoder, config, tokenizer, args):
        super().__init__(encoder, config, tokenizer, args, clr_mask=False)
        
    def forward(self, input_ids=None, labels=None): 
        attention_mask = input_ids.ne(1)
        outputs = self.encoder(input_ids,attention_mask)
        cls_output = self.cls_head(outputs[0])
        logits=cls_output
        prob=torch.sigmoid(logits)
        return prob

     
class DefectModel(nn.Module):
    def __init__(self, encoder, config, tokenizer, args):
        super(DefectModel, self).__init__()
        self.encoder = encoder
        self.config = config
        self.tokenizer = tokenizer
        self.classifier = nn.Linear(config.hidden_size, 2)
        self.args = args

    def get_t5_vec(self, source_ids):
        attention_mask = source_ids.ne(self.tokenizer.pad_token_id)
        outputs = self.encoder(input_ids=source_ids, attention_mask=attention_mask,
                               labels=source_ids, decoder_attention_mask=attention_mask, output_hidden_states=True)
        hidden_states = outputs['decoder_hidden_states'][-1]
        eos_mask = source_ids.eq(self.config.eos_token_id)

        if len(torch.unique(eos_mask.sum(1))) > 1:
            print(eos_mask.sum(1))
            print(torch.unique(eos_mask.sum(1)))
            raise ValueError("All examples must have the same number of <eos> tokens.")
        vec = hidden_states[eos_mask, :].view(hidden_states.size(0), -1,
                                              hidden_states.size(-1))[:, -1, :]
        return vec

    def get_bart_vec(self, source_ids):
        attention_mask = source_ids.ne(self.tokenizer.pad_token_id)
        outputs = self.encoder(input_ids=source_ids, attention_mask=attention_mask,
                               labels=source_ids, decoder_attention_mask=attention_mask, output_hidden_states=True)
        hidden_states = outputs['decoder_hidden_states'][-1]
        eos_mask = source_ids.eq(self.config.eos_token_id)

        if len(torch.unique(eos_mask.sum(1))) > 1:
            raise ValueError("All examples must have the same number of <eos> tokens.")
        vec = hidden_states[eos_mask, :].view(hidden_states.size(0), -1,
                                              hidden_states.size(-1))[:, -1, :]
        return vec

    def get_roberta_vec(self, source_ids):
        attention_mask = source_ids.ne(self.tokenizer.pad_token_id)
        vec = self.encoder(input_ids=source_ids, attention_mask=attention_mask)[0][:, 0, :]
        return vec

    def forward(self, source_ids=None, labels=None, weight=None):

        if self.args.model_type == 'codet5':
            vec = self.get_t5_vec(source_ids)
        elif self.args.model_type == 'bart':
            vec = self.get_bart_vec(source_ids)
        elif self.args.model_type == 'roberta':
            vec = self.get_roberta_vec(source_ids)
        elif self.args.model_type == 't5':
            vec = self.get_t5_vec(source_ids)
        
        logits = self.classifier(vec)
        prob = nn.functional.softmax(logits)

        if labels is not None:
            loss_fct = nn.CrossEntropyLoss(weight=weight)
            loss = loss_fct(logits, labels)
            return loss, prob
        else:
            return prob


class DecoderClassifier(nn.Module):
    def __init__(self, encoder, config, tokenizer, args):
        super(DecoderClassifier, self).__init__()
        self.encoder = encoder
        self.config=config
        self.tokenizer=tokenizer
        self.args=args
        self.classifier = nn.Linear(config.hidden_size, 2)
        
    def forward(self, input_ids=None, labels=None, weight=None):
        attention_mask = input_ids.ne(self.tokenizer.pad_token_id)
        outputs = self.encoder(input_ids, attention_mask=attention_mask)
        hidden_states = outputs[0]
        logits = self.classifier(hidden_states)

        batch_size = input_ids.size(0)
        if self.config.pad_token_id is None and batch_size != 1:
            raise ValueError("Cannot handle batch sizes > 1 if no padding token is defined.")
        if self.config.pad_token_id is None:
            sequence_lengths = -1
        else:
            if input_ids is not None:
                sequence_lengths = torch.eq(input_ids, self.config.pad_token_id).int().argmax(-1) - 1
                sequence_lengths = sequence_lengths % input_ids.shape[-1]
                sequence_lengths = sequence_lengths.to(logits.device)
            else:
                sequence_lengths = -1

        pooled_logits = logits[torch.arange(batch_size, device=logits.device), sequence_lengths]
        prob = nn.functional.softmax(pooled_logits, dim=-1)


        if labels is not None:
            labels = labels.to(logits.device)
            loss_fct = nn.CrossEntropyLoss(weight=weight)

            loss = loss_fct(pooled_logits.view(-1, 2), labels.view(-1))
            return loss, prob
        else:
            return prob