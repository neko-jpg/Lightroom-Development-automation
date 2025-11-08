"""
AI Selection Engine

Integrates image quality evaluation with EXIF analysis and context recognition
to provide comprehensive photo selection and rating.

Includes LLM-based comprehensive evaluation using Ollama for intelligent
photo assessment and tag generation.

Requirements: 2.1, 2.2, 2.3, 2.5
"""

import logging
from typing import Dict, Optional, List
from pathlib import Path
import json

from image_quality_evaluator import ImageQualityEvaluator
from exif_analyzer import EXIFAnalyzer
from context_engine import ContextEngine
from ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AISelector:
    """
    AI-powered photo selection engine that combines:
    - Image quality evaluation (focus, exposure, composition)
    - EXIF metadata analysis
    - Context recognition
    - LLM-based comprehensive evaluation using Ollama
    """
    
    def __init__(
        self,
        quality_evaluator: Optional[ImageQualityEvaluator] = None,
        exif_analyzer: Optional[EXIFAnalyzer] = None,
        context_engine: Optional[ContextEngine] = None,
        ollama_client: Optional[OllamaClient] = None,
        enable_llm: bool = True,
        llm_model: str = "llama3.1:8b-instruct"
    ):
        """
        Initialize AI Selector.
        
        Args:
            quality_evaluator: Image quality evaluator instance
            exif_analyzer: EXIF analyzer instance
            context_engine: Context recognition engine instance
            ollama_client: Ollama client for LLM evaluation
            enable_llm: Enable LLM-based evaluation (default: True)
            llm_model: LLM model to use (default: llama3.1:8b-instruct)
        """
        self.quality_evaluator = quality_evaluator or ImageQualityEvaluator()
        self.exif_analyzer = exif_analyzer or EXIFAnalyzer()
        self.context_engine = context_engine or ContextEngine()
        self.ollama_client = ollama_client or OllamaClient()
        self.enable_llm = enable_llm
        self.llm_model = llm_model
        
        logger.info(f"AI Selector initialized (LLM: {enable_llm}, Model: {llm_model})")
    
    def evaluate(self, image_path: str) -> Dict:
        """
        Perform comprehensive photo evaluation.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing:
            {
                'overall_score': float (1-5 stars),
                'quality': Dict (focus, exposure, composition scores),
                'exif': Dict (camera settings, metadata),
                'context': Dict (scene type, lighting, subject),
                'recommendation': str (approve/review/reject),
                'tags': List[str] (suggested tags),
                'llm_evaluation': Dict (LLM-based assessment, if enabled)
            }
        """
        try:
            logger.info(f"Evaluating photo: {image_path}")
            
            # 1. Image quality evaluation
            quality_results = self.quality_evaluator.evaluate(image_path)
            
            # 2. EXIF analysis
            exif_data = self.exif_analyzer.analyze(image_path)
            
            # 3. Context recognition
            context = self.context_engine.determine_context(exif_data, quality_results)
            
            # 4. LLM-based comprehensive evaluation (if enabled)
            llm_evaluation = None
            if self.enable_llm:
                try:
                    llm_evaluation = self._llm_evaluate(
                        quality_results,
                        exif_data,
                        context,
                        image_path
                    )
                except Exception as e:
                    logger.warning(f"LLM evaluation failed: {e}, continuing with basic evaluation")
            
            # 5. Calculate final score (incorporating LLM if available)
            final_score = self._calculate_final_score(
                quality_results,
                exif_data,
                context,
                llm_evaluation
            )
            
            # 6. Generate recommendation (incorporating LLM if available)
            recommendation = self._generate_recommendation(
                final_score,
                quality_results,
                llm_evaluation
            )
            
            # 7. Generate suggested tags (incorporating LLM if available)
            tags = self._generate_tags(
                quality_results,
                exif_data,
                context,
                llm_evaluation
            )
            
            result = {
                'overall_score': round(final_score, 2),
                'quality': {
                    'focus_score': quality_results['focus_score'],
                    'exposure_score': quality_results['exposure_score'],
                    'composition_score': quality_results['composition_score'],
                    'faces_detected': quality_results['faces_detected']
                },
                'exif': exif_data,
                'context': context,
                'recommendation': recommendation,
                'tags': tags,
                'metrics': {
                    'quality_metrics': quality_results['metrics'],
                    'exif_hints': exif_data.get('context_hints', {})
                }
            }
            
            # Add LLM evaluation if available
            if llm_evaluation:
                result['llm_evaluation'] = llm_evaluation
            
            logger.info(f"Evaluation complete: {final_score:.2f} stars - {recommendation}")
            return result
        
        except Exception as e:
            logger.error(f"Error evaluating photo {image_path}: {e}")
            raise
    
    def _llm_evaluate(
        self,
        quality_results: Dict,
        exif_data: Dict,
        context: Dict,
        image_path: str
    ) -> Dict:
        """
        Perform LLM-based comprehensive photo evaluation.
        
        Args:
            quality_results: Image quality evaluation results
            exif_data: EXIF metadata
            context: Context recognition results
            image_path: Path to the image file
            
        Returns:
            Dictionary containing:
            {
                'llm_score': float (1-5),
                'reasoning': str,
                'suggested_tags': List[str],
                'strengths': List[str],
                'weaknesses': List[str]
            }
        """
        # Build comprehensive prompt for LLM
        prompt = self._build_evaluation_prompt(quality_results, exif_data, context)
        
        # Call Ollama API
        try:
            response = self.ollama_client.generate(
                model=self.llm_model,
                prompt=prompt,
                temperature=0.2,  # Low temperature for consistent evaluation
                max_tokens=500
            )
            
            # Parse LLM response
            evaluation = self._parse_llm_response(response)
            
            logger.info(f"LLM evaluation: {evaluation['llm_score']:.2f} stars")
            return evaluation
            
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            raise
    
    def _build_evaluation_prompt(
        self,
        quality_results: Dict,
        exif_data: Dict,
        context: Dict
    ) -> str:
        """
        Build evaluation prompt for LLM.
        
        Args:
            quality_results: Image quality evaluation results
            exif_data: EXIF metadata
            context: Context recognition results
            
        Returns:
            Formatted prompt string
        """
        prompt = """あなたはプロの写真評論家です。以下の写真分析データに基づいて、総合的な評価を行ってください。

## 画質評価
- フォーカススコア: {focus_score:.2f}/5.0 ({focus_category})
- 露出スコア: {exposure_score:.2f}/5.0 ({exposure_category})
- 構図スコア: {composition_score:.2f}/5.0 ({composition_category})
- 検出された顔: {faces_detected}人

## 撮影情報
- カメラ: {camera_make} {camera_model}
- レンズ: {lens}
- ISO: {iso}
- 絞り: f/{aperture}
- シャッター速度: {shutter_speed}
- 焦点距離: {focal_length}mm

## コンテキスト
- 被写体タイプ: {subject_type}
- 照明条件: {lighting}
- 撮影場所: {location}
- 時間帯: {time_of_day}

以下の形式で評価してください：

SCORE: [1-5の数値]
REASONING: [評価の理由を2-3文で]
STRENGTHS: [長所をカンマ区切りで3つまで]
WEAKNESSES: [短所をカンマ区切りで3つまで]
TAGS: [推奨タグをカンマ区切りで5つまで]
"""
        
        # Extract metrics
        focus_metrics = quality_results['metrics']['focus']
        exposure_metrics = quality_results['metrics']['exposure']
        composition_metrics = quality_results['metrics']['composition']
        
        # Extract camera info
        camera = exif_data.get('camera', {})
        settings = exif_data.get('settings', {})
        
        # Format prompt
        formatted_prompt = prompt.format(
            focus_score=quality_results['focus_score'],
            focus_category=focus_metrics.get('sharpness_category', 'unknown'),
            exposure_score=quality_results['exposure_score'],
            exposure_category=exposure_metrics.get('exposure_category', 'unknown'),
            composition_score=quality_results['composition_score'],
            composition_category=composition_metrics.get('composition_category', 'unknown'),
            faces_detected=quality_results['faces_detected'],
            camera_make=camera.get('make', 'Unknown'),
            camera_model=camera.get('model', 'Unknown'),
            lens=settings.get('lens_model', 'Unknown'),
            iso=settings.get('iso', 'Unknown'),
            aperture=settings.get('aperture', 'Unknown'),
            shutter_speed=settings.get('shutter_speed', 'Unknown'),
            focal_length=settings.get('focal_length', 'Unknown'),
            subject_type=context.get('subject_type', 'unknown'),
            lighting=context.get('lighting', 'unknown'),
            location=context.get('location', 'unknown'),
            time_of_day=context.get('time_of_day', 'unknown')
        )
        
        return formatted_prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        Parse LLM evaluation response.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Parsed evaluation dictionary
        """
        evaluation = {
            'llm_score': 3.0,  # Default
            'reasoning': '',
            'suggested_tags': [],
            'strengths': [],
            'weaknesses': []
        }
        
        try:
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('SCORE:'):
                    score_str = line.replace('SCORE:', '').strip()
                    try:
                        score = float(score_str)
                        evaluation['llm_score'] = max(1.0, min(5.0, score))
                    except ValueError:
                        logger.warning(f"Could not parse score: {score_str}")
                
                elif line.startswith('REASONING:'):
                    evaluation['reasoning'] = line.replace('REASONING:', '').strip()
                
                elif line.startswith('STRENGTHS:'):
                    strengths_str = line.replace('STRENGTHS:', '').strip()
                    evaluation['strengths'] = [
                        s.strip() for s in strengths_str.split(',') if s.strip()
                    ]
                
                elif line.startswith('WEAKNESSES:'):
                    weaknesses_str = line.replace('WEAKNESSES:', '').strip()
                    evaluation['weaknesses'] = [
                        w.strip() for w in weaknesses_str.split(',') if w.strip()
                    ]
                
                elif line.startswith('TAGS:'):
                    tags_str = line.replace('TAGS:', '').strip()
                    evaluation['suggested_tags'] = [
                        t.strip() for t in tags_str.split(',') if t.strip()
                    ]
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
        
        return evaluation
    
    def _calculate_final_score(
        self,
        quality_results: Dict,
        exif_data: Dict,
        context: Dict,
        llm_evaluation: Optional[Dict] = None
    ) -> float:
        """
        Calculate final 1-5 star rating.
        
        Combines quality scores with EXIF, context, and LLM evaluation.
        
        Args:
            quality_results: Image quality evaluation results
            exif_data: EXIF metadata
            context: Context recognition results
            llm_evaluation: Optional LLM evaluation results
            
        Returns:
            Final score (1.0-5.0)
        """
        # Base score from quality evaluation
        base_score = quality_results['overall_score']
        
        # Adjustments based on EXIF data
        exif_adjustment = 0.0
        
        # Bonus for good camera settings
        if 'settings' in exif_data:
            settings = exif_data['settings']
            
            # Appropriate ISO usage
            iso = settings.get('iso', 0)
            if iso > 0:
                if iso <= 800:
                    exif_adjustment += 0.1  # Good ISO
                elif iso > 3200:
                    exif_adjustment -= 0.1  # High ISO (potential noise)
            
            # Appropriate aperture for subject
            aperture = settings.get('aperture', 0)
            if aperture > 0:
                if context.get('subject_type') == 'portrait' and aperture <= 2.8:
                    exif_adjustment += 0.1  # Good portrait aperture
                elif context.get('subject_type') == 'landscape' and aperture >= 8.0:
                    exif_adjustment += 0.1  # Good landscape aperture
        
        # Context-based adjustments
        context_adjustment = 0.0
        
        # Bonus for challenging conditions handled well
        if context.get('lighting') == 'low_light' and quality_results['exposure_score'] >= 3.5:
            context_adjustment += 0.2  # Good low-light handling
        
        if context.get('lighting') == 'backlit' and quality_results['exposure_score'] >= 3.5:
            context_adjustment += 0.2  # Good backlight handling
        
        # Calculate base final score
        final_score = base_score + exif_adjustment + context_adjustment
        
        # Incorporate LLM evaluation if available (weighted blend)
        if llm_evaluation and 'llm_score' in llm_evaluation:
            llm_score = llm_evaluation['llm_score']
            # Blend: 70% technical metrics, 30% LLM judgment
            final_score = (final_score * 0.7) + (llm_score * 0.3)
            logger.debug(f"Blended score: technical={final_score*0.7:.2f}, llm={llm_score*0.3:.2f}")
        
        # Clamp to 1.0-5.0 range
        final_score = max(1.0, min(5.0, final_score))
        
        return final_score
    
    def _generate_recommendation(
        self,
        score: float,
        quality_results: Dict,
        llm_evaluation: Optional[Dict] = None
    ) -> str:
        """
        Generate recommendation based on score, quality metrics, and LLM insights.
        
        Args:
            score: Overall score (1-5)
            quality_results: Quality evaluation results
            llm_evaluation: Optional LLM evaluation results
            
        Returns:
            Recommendation string: 'approve', 'review', or 'reject'
        """
        # Consider LLM weaknesses if available
        critical_weaknesses = []
        if llm_evaluation and 'weaknesses' in llm_evaluation:
            weaknesses = llm_evaluation['weaknesses']
            # Check for critical issues mentioned by LLM
            critical_keywords = ['ぼけ', 'ブレ', 'blur', 'out of focus', '露出オーバー', 'overexposed']
            for weakness in weaknesses:
                if any(keyword in weakness.lower() for keyword in critical_keywords):
                    critical_weaknesses.append(weakness)
        
        # High quality - auto-approve
        if score >= 4.0 and not critical_weaknesses:
            return 'approve'
        
        # Good quality but check for specific issues
        elif score >= 3.0:
            # Check for critical quality issues
            if quality_results['focus_score'] < 2.5 or critical_weaknesses:
                return 'reject'  # Too blurry or critical issues
            elif quality_results['exposure_score'] < 2.5:
                return 'review'  # Exposure issues - may be fixable
            else:
                return 'review'  # Generally good, needs review
        
        # Low quality - reject
        else:
            return 'reject'
    
    def _generate_tags(
        self,
        quality_results: Dict,
        exif_data: Dict,
        context: Dict,
        llm_evaluation: Optional[Dict] = None
    ) -> list:
        """
        Generate suggested tags based on analysis and LLM suggestions.
        
        Args:
            quality_results: Quality evaluation results
            exif_data: EXIF metadata
            context: Context recognition results
            llm_evaluation: Optional LLM evaluation results
            
        Returns:
            List of suggested tags
        """
        tags = []
        
        # Quality-based tags
        if quality_results['overall_score'] >= 4.5:
            tags.append('excellent_quality')
        elif quality_results['overall_score'] >= 4.0:
            tags.append('high_quality')
        
        # Focus tags
        focus_category = quality_results['metrics']['focus']['sharpness_category']
        if focus_category in ['sharp', 'very_sharp']:
            tags.append('sharp')
        
        # Exposure tags
        exposure_category = quality_results['metrics']['exposure']['exposure_category']
        if exposure_category == 'well_exposed':
            tags.append('well_exposed')
        
        # Composition tags
        composition_category = quality_results['metrics']['composition']['composition_category']
        if composition_category in ['excellent', 'good']:
            tags.append('good_composition')
        
        # Face detection tags
        if quality_results['faces_detected'] > 0:
            tags.append('portrait')
            if quality_results['faces_detected'] == 1:
                tags.append('single_person')
            else:
                tags.append('group')
        
        # Context-based tags
        if context.get('subject_type'):
            tags.append(context['subject_type'])
        
        if context.get('lighting'):
            tags.append(f"{context['lighting']}_lighting")
        
        if context.get('location'):
            tags.append(context['location'])
        
        # Camera-based tags
        if 'camera' in exif_data:
            camera = exif_data['camera']
            if camera.get('make'):
                tags.append(camera['make'].lower().replace(' ', '_'))
        
        # Add LLM-suggested tags if available
        if llm_evaluation and 'suggested_tags' in llm_evaluation:
            llm_tags = llm_evaluation['suggested_tags']
            # Add unique LLM tags (avoid duplicates)
            for tag in llm_tags:
                normalized_tag = tag.lower().replace(' ', '_')
                if normalized_tag not in tags:
                    tags.append(normalized_tag)
        
        return tags
    
    def batch_evaluate(self, image_paths: list) -> list:
        """
        Evaluate multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of evaluation results
        """
        results = []
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"Processing {i}/{len(image_paths)}: {Path(image_path).name}")
            
            try:
                result = self.evaluate(image_path)
                result['file_path'] = image_path
                results.append(result)
            
            except Exception as e:
                logger.error(f"Failed to evaluate {image_path}: {e}")
                results.append({
                    'file_path': image_path,
                    'error': str(e),
                    'overall_score': 0.0,
                    'recommendation': 'error'
                })
        
        return results
    
    def filter_by_quality(
        self,
        image_paths: list,
        min_score: float = 3.5
    ) -> list:
        """
        Filter images by minimum quality score.
        
        Args:
            image_paths: List of image file paths
            min_score: Minimum score threshold (default: 3.5)
            
        Returns:
            List of image paths that meet the quality threshold
        """
        results = self.batch_evaluate(image_paths)
        
        filtered = [
            r['file_path']
            for r in results
            if r.get('overall_score', 0) >= min_score
        ]
        
        logger.info(f"Filtered {len(filtered)}/{len(image_paths)} images (min_score={min_score})")
        
        return filtered


def main():
    """Example usage of AI Selector."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ai_selector.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Initialize AI Selector
    selector = AISelector()
    
    # Evaluate image
    print(f"Evaluating: {image_path}\n")
    result = selector.evaluate(image_path)
    
    # Print results
    print("=" * 60)
    print("AI SELECTION RESULTS")
    print("=" * 60)
    print(f"\nOverall Score: {result['overall_score']:.2f} / 5.0")
    print(f"Recommendation: {result['recommendation'].upper()}")
    
    print(f"\nQuality Scores:")
    print(f"  Focus: {result['quality']['focus_score']:.2f}")
    print(f"  Exposure: {result['quality']['exposure_score']:.2f}")
    print(f"  Composition: {result['quality']['composition_score']:.2f}")
    print(f"  Faces Detected: {result['quality']['faces_detected']}")
    
    print(f"\nContext:")
    for key, value in result['context'].items():
        print(f"  {key}: {value}")
    
    print(f"\nSuggested Tags:")
    print(f"  {', '.join(result['tags'])}")


if __name__ == '__main__':
    main()
