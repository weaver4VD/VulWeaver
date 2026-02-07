"""
PrimeVul Dataset Context Generation Tool
Convert PrimeVul structured context data to string format similar to vulnerability-reproduction-zh
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from complete_dataset_reader import PrimeVulCompleteDatasetReader, DatasetSample


class PrimeVulContextGenerator:
    """PrimeVul Context Generator"""
    
    def __init__(self, reader: Optional[PrimeVulCompleteDatasetReader] = None):
        """
        Initialize context generator
        
        Args:
            reader: PrimeVul dataset reader, if None, create a new one
        """
        self.reader = reader or PrimeVulCompleteDatasetReader()
    
    def generate_context_string(self, sample: DatasetSample) -> str:
        """
        Generate context string similar to vulnerability-reproduction-zh
        
        Args:
            sample: PrimeVul data sample
            
        Returns:
            Concatenated context string
        """
        if not sample.analysis_result:
            return ""
        
        context_parts = []
        analysis = sample.analysis_result
        if analysis.get('importContext'):
            context_parts.append("// Import Context:")
            for imp in analysis['importContext']:
                context_parts.append(f"{imp}")
            context_parts.append("")
        if analysis.get('globalVars'):
            context_parts.append("// Global Variables:")
            for var in analysis['globalVars']:
                context_parts.append(f"{var};")
            context_parts.append("")
        if analysis.get('typeDefs'):
            context_parts.append("// Type Definitions:")
            for typedef in analysis['typeDefs']:
                if len(typedef) >= 2:
                    context_parts.append(f"// {typedef[1]}:")
                    context_parts.append(f"{typedef[0]}")
                    context_parts.append("")
        if analysis.get('calleeMethods'):
            context_parts.append("// Called Methods (top 10):")
            for i, method in enumerate(analysis['calleeMethods'][:10]):
                if len(method) >= 3:
                    context_parts.append(f"// {method[1]} from {method[0]}:")
                    context_parts.append(f"{method[2]}")
                    context_parts.append("")
        
        return "\n".join(context_parts)
    
    def convert_to_zh_format(self, sample: DatasetSample) -> Dict:
        """
        Convert PrimeVul sample to format similar to vulnerability-reproduction-zh
        
        Args:
            sample: PrimeVul data sample
            
        Returns:
            Converted format dictionary
        """
        vuln_code = sample.vulnerable_sample.get('func', '')
        fixed_code = sample.fixed_sample.get('func', '')
        context_str = self.generate_context_string(sample)
        
        return {
            "repository": sample.project,
            "cve_id": sample.vulnerable_sample.get('cve', ''),
            "cwe_list": sample.vulnerable_sample.get('cwe', []),
            "commit_hash": sample.commit_id,
            "short_hash": sample.commit_id[:8],
            "vulnerableMethods_before": [{
                "filename": sample.vulnerable_sample.get('file_name', ''),
                "method_name": "vulnerable_function",
                "raw_code": vuln_code,
                "start_line": 1
            }],
            "vulnerableMethods_after": [{
                "filename": sample.fixed_sample.get('file_name', ''),
                "method_name": "fixed_function", 
                "raw_code": fixed_code,
                "start_line": 1
            }],
            "code_context": context_str
        }
    
    def generate_all_contexts(self, output_file: str = "primevul_with_context.json", include_no_context: bool = True) -> List[Dict]:
        """
        Generate context strings for all PrimeVul samples (including samples without context)
        
        Args:
            output_file: Output file path
            include_no_context: Whether to include samples without context
            
        Returns:
            List of converted samples
        """
        print("🚀 Starting to generate PrimeVul context strings...")
        all_samples = self.reader.load_all_samples()
        samples_with_context = self.reader.get_samples_with_context()
        samples_without_context = self.reader.get_samples_without_context()
        
        print(f"📊 Total samples: {len(all_samples)}")
        print(f"📊 Samples with context: {len(samples_with_context)}")
        print(f"📊 Samples without context: {len(samples_without_context)}")
        
        converted_samples = []
        print("  Processing samples with context...")
        for i, sample in enumerate(samples_with_context):
            try:
                converted = self.convert_to_zh_format(sample)
                converted_samples.append(converted)
                
                if (i + 1) % 100 == 0:
                    print(f"    Samples with context progress: {i + 1}/{len(samples_with_context)}")
                    
            except Exception as e:
                print(f"❌ Failed to process sample with context: {sample.file_path} - {e}")
        if include_no_context:
            print("  Processing samples without context...")
            for i, sample in enumerate(samples_without_context):
                try:
                    converted = self.convert_to_zh_format(sample)
                    converted_samples.append(converted)
                    
                    if (i + 1) % 100 == 0:
                        print(f"    Samples without context progress: {i + 1}/{len(samples_without_context)}")
                        
                except Exception as e:
                    print(f"❌ Failed to process sample without context: {sample.file_path} - {e}")
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted_samples, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully generated {len(converted_samples)} samples")
        print(f"  - With context: {len(samples_with_context)}")
        if include_no_context:
            print(f"  - Without context: {len(samples_without_context)}")
        print(f"💾 Results saved to: {output_path.absolute()}")
        
        return converted_samples
    
    def compare_context_quality(self, sample: DatasetSample) -> Dict:
        """
        Evaluate context quality
        
        Args:
            sample: PrimeVul data sample
            
        Returns:
            Context quality evaluation results
        """
        if not sample.analysis_result:
            return {
                "has_context": False,
                "quality_score": 0,
                "details": "No context data"
            }
        
        analysis = sample.analysis_result
        score = 0
        details = []
        if analysis.get('importContext'):
            score += 20
            details.append(f"Import Context: {len(analysis['importContext'])} items")
        
        if analysis.get('globalVars'):
            score += 15
            details.append(f"Global Variables: {len(analysis['globalVars'])} items")
        
        if analysis.get('typeDefs'):
            score += 25
            details.append(f"Type Definitions: {len(analysis['typeDefs'])} items")
        
        if analysis.get('calleeMethods'):
            score += 40
            details.append(f"Called Methods: {len(analysis['calleeMethods'])} items")
        
        return {
            "has_context": True,
            "quality_score": score,
            "details": "; ".join(details),
            "context_length": len(self.generate_context_string(sample))
        }
    
    def analyze_context_coverage(self) -> Dict:
        """
        Analyze context coverage for the entire dataset
        
        Returns:
            Context coverage analysis results
        """
        print("🔍 Analyzing PrimeVul dataset context coverage...")
        
        all_samples = self.reader.load_all_samples()
        samples_with_context = self.reader.get_samples_with_context()
        samples_without_context = self.reader.get_samples_without_context()
        
        quality_scores = []
        context_stats = {
            "has_imports": 0,
            "has_globals": 0,
            "has_typedefs": 0,
            "has_callees": 0,
            "high_quality": 0
        }
        
        for sample in samples_with_context:
            quality = self.compare_context_quality(sample)
            quality_scores.append(quality['quality_score'])
            
            if sample.analysis_result:
                analysis = sample.analysis_result
                if analysis.get('importContext'):
                    context_stats["has_imports"] += 1
                if analysis.get('globalVars'):
                    context_stats["has_globals"] += 1
                if analysis.get('typeDefs'):
                    context_stats["has_typedefs"] += 1
                if analysis.get('calleeMethods'):
                    context_stats["has_callees"] += 1
                if quality['quality_score'] >= 80:
                    context_stats["high_quality"] += 1
        
        return {
            "total_samples": len(all_samples),
            "samples_with_context": len(samples_with_context),
            "samples_without_context": len(samples_without_context),
            "context_coverage_ratio": len(samples_with_context) / len(all_samples) * 100,
            "no_context_ratio": len(samples_without_context) / len(all_samples) * 100,
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "context_component_stats": context_stats,
            "high_quality_ratio": context_stats["high_quality"] / len(samples_with_context) * 100 if samples_with_context else 0
        }
    
    def print_context_analysis(self):
        """Print context analysis results"""
        analysis = self.analyze_context_coverage()
        
        print("\n" + "="*60)
        print("📊 PrimeVul Dataset Context Analysis Report")
        print("="*60)
        
        print(f"Total samples: {analysis['total_samples']}")
        print(f"Samples with context: {analysis['samples_with_context']}")
        print(f"Samples without context: {analysis['samples_without_context']}")
        print(f"Context coverage ratio: {analysis['context_coverage_ratio']:.1f}%")
        print(f"No context ratio: {analysis['no_context_ratio']:.1f}%")
        print(f"Average quality score: {analysis['average_quality_score']:.1f}/100")
        print(f"High quality samples ratio: {analysis['high_quality_ratio']:.1f}%")
        
        print(f"\nContext component statistics:")
        stats = analysis['context_component_stats']
        total_with_context = analysis['samples_with_context']
        
        if total_with_context > 0:
            print(f"  - Contains Import Context: {stats['has_imports']} ({stats['has_imports']/total_with_context*100:.1f}%)")
            print(f"  - Contains Global Variables: {stats['has_globals']} ({stats['has_globals']/total_with_context*100:.1f}%)")
            print(f"  - Contains Type Definitions: {stats['has_typedefs']} ({stats['has_typedefs']/total_with_context*100:.1f}%)")
            print(f"  - Contains Called Methods: {stats['has_callees']} ({stats['has_callees']/total_with_context*100:.1f}%)")
            print(f"  - High quality samples (≥80 points): {stats['high_quality']} ({stats['high_quality']/total_with_context*100:.1f}%)")


def demo_context_generation():
    """Demonstrate context generation functionality"""
    print("🎯 PrimeVul Context Generation Demo")
    print("=" * 50)
    generator = PrimeVulContextGenerator()
    generator.print_context_analysis()
    samples_with_context = generator.reader.get_samples_with_context()
    
    if samples_with_context:
        print(f"\n📖 Context generation example:")
        sample = samples_with_context[0]
        
        print(f"Project: {sample.project}")
        print(f"CVE: {sample.vulnerable_sample.get('cve', 'N/A')}")
        context_str = generator.generate_context_string(sample)
        quality = generator.compare_context_quality(sample)
        
        print(f"Context quality score: {quality['quality_score']}/100")
        print(f"Context details: {quality['details']}")
        print(f"Context length: {quality['context_length']} characters")
        
        if context_str:
            print(f"\nGenerated context string preview (first 500 characters):")
            print("-" * 40)
            print(context_str[:500] + ("..." if len(context_str) > 500 else ""))
        zh_format = generator.convert_to_zh_format(sample)
        print(f"\nFields converted to zh format:")
        print(f"  - repository: {zh_format['repository']}")
        print(f"  - cve_id: {zh_format['cve_id']}")
        print(f"  - commit_hash: {zh_format['commit_hash']}")
        print(f"  - vulnerableMethods_before count: {len(zh_format['vulnerableMethods_before'])}")
        print(f"  - vulnerableMethods_after count: {len(zh_format['vulnerableMethods_after'])}")
        print(f"  - code_context length: {len(zh_format['code_context'])} characters")
    
    return generator


if __name__ == "__main__":


    generator = PrimeVulContextGenerator()
    all_samples = generator.generate_all_contexts(
        "primevul_zh_format_complete.json",
        include_no_context=True
    )
    context_only = generator.generate_all_contexts(
        "primevul_zh_format_context_only.json",
        include_no_context=False
    )
