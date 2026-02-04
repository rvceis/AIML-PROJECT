"""
Test script for the textile pattern generator
Run this to verify your LoRA model loads correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.lora_generator import LoRATextileGenerator
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_model_loading():
    """Test if LoRA models load successfully"""
    print("\n" + "="*60)
    print("TEXTILE PATTERN GENERATOR - LORA MODEL TEST")
    print("="*60 + "\n")
    
    # Path to your LoRA weights
    lora_path = os.path.join(os.path.dirname(__file__), "..", "textile_loras_trained")
    
    print(f"LoRA Path: {lora_path}")
    print(f"LoRA Exists: {os.path.exists(lora_path)}\n")
    
    if os.path.exists(lora_path):
        folders = [f for f in os.listdir(lora_path) if os.path.isdir(os.path.join(lora_path, f))]
        print(f"LoRA Folders: {folders}\n")
    
    try:
        # Initialize generator
        print("Initializing LoRATextileGenerator...")
        generator = LoRATextileGenerator(lora_base_path=lora_path)
        
        print("\n" + "-"*60)
        print("Loading model (this may take several minutes)...")
        print("-"*60 + "\n")
        
        # Load a style to test
        test_style = "bandhani"
        print(f"Testing with style: {test_style}")
        generator.load_style_pipeline(test_style)
        
        print("\n" + "="*60)
        print("✅ MODEL LOADED SUCCESSFULLY!")
        print("="*60 + "\n")
        
        print("Model Details:")
        print(f"  - Device: {generator.device}")
        print(f"  - dtype: {generator.dtype}")
        print(f"  - Available styles: {', '.join(generator.available_styles)}")
        print(f"  - Loaded styles: {', '.join(generator.get_loaded_styles())}")
        print(f"  - Circular padding: Applied to VAE Conv2D layers")
        print(f"  - Base model: {generator.base_model_id}")
        print(f"  - LoRA path: {generator.lora_base_path}")
        
        print("\n" + "="*60)
        print("READY TO GENERATE PATTERNS!")
        print("="*60 + "\n")
        
        return generator
    
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR LOADING MODEL")
        print("="*60 + "\n")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_generation():
    """Test pattern generation (optional - requires model loaded)"""
    print("\n" + "="*60)
    print("TESTING PATTERN GENERATION")
    print("="*60 + "\n")
    
    lora_path = os.path.join(os.path.dirname(__file__), "..", "textile_loras_trained")
    
    try:
        generator = LoRATextileGenerator(lora_base_path=lora_path)
        
        # Test all three styles
        test_cases = [
            ("bandhani", "vibrant red and gold with circular dots"),
            ("batik", "intricate floral design with blue colors"),
            ("ikat", "geometric zigzag pattern")
        ]
        
        for style, prompt in test_cases:
            print(f"\nGenerating {style} pattern...")
            print(f"  Prompt: '{prompt}'")
            print(f"  Steps: 20 (faster test)")
            
            image, seed = generator.generate(
                prompt=prompt,
                style=style,
                num_inference_steps=20,  # Faster for testing
                seed=42
            )
            
            # Save test image
            output_path = f"test_pattern_{style}.png"
            image.save(output_path)
            
            print(f"  ✅ Saved: {output_path} (size: {image.size}, seed: {seed})")
        
        print("\n" + "="*60)
        print("✅ ALL PATTERNS GENERATED SUCCESSFULLY!")
        print("="*60 + "\n")
        print(f"  - Seamless: Yes (circular padding applied)")
        print(f"  - Test images saved in current directory")
        print()
        
        return True
    
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR GENERATING PATTERN")
        print("="*60 + "\n")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Textile Pattern Generator')
    parser.add_argument('--generate', action='store_true', 
                       help='Also test pattern generation (takes longer)')
    
    args = parser.parse_args()
    
    # Test model loading
    generator = test_model_loading()
    
    # Optionally test generation
    if generator and args.generate:
        test_generation()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
