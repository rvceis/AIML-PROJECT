"""
Pre-flight check for LoRA integration
Verifies all requirements before starting the backend
"""

import os
import sys
from pathlib import Path

def check_mark(condition):
    return "✅" if condition else "❌"

def verify_setup():
    """Run pre-flight checks"""
    
    print("="*70)
    print("LORA INTEGRATION - PRE-FLIGHT CHECK")
    print("="*70)
    print()
    
    checks_passed = 0
    checks_total = 0
    issues = []
    
    # 1. Check Python version
    checks_total += 1
    python_version = sys.version_info
    python_ok = python_version.major == 3 and python_version.minor >= 8
    print(f"{check_mark(python_ok)} Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_ok:
        checks_passed += 1
    else:
        issues.append("Python 3.8+ required")
    
    # 2. Check dependencies
    print()
    print("Checking dependencies:")
    required_packages = [
        'torch',
        'diffusers',
        'transformers',
        'peft',
        'PIL',
        'flask',
        'flask_sqlalchemy',
        'flask_jwt_extended'
    ]
    
    for package in required_packages:
        checks_total += 1
        try:
            if package == 'PIL':
                __import__('PIL')
            else:
                __import__(package)
            print(f"  ✅ {package}")
            checks_passed += 1
        except ImportError:
            print(f"  ❌ {package} - NOT FOUND")
            issues.append(f"Install {package}: pip install {package}")
    
    # 3. Check CUDA
    print()
    checks_total += 1
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"{check_mark(cuda_available)} CUDA GPU: ", end="")
        if cuda_available:
            print(f"{torch.cuda.get_device_name(0)}")
            print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            checks_passed += 1
        else:
            print("Not available (will use CPU - slower)")
            issues.append("GPU recommended for faster generation")
    except:
        print("❌ Cannot check CUDA")
    
    # 4. Check LoRA models directory
    print()
    print("Checking LoRA models:")
    checks_total += 1
    
    backend_dir = Path(__file__).parent
    lora_base = backend_dir.parent / "textile_loras_trained"
    
    lora_exists = lora_base.exists() and lora_base.is_dir()
    print(f"{check_mark(lora_exists)} LoRA directory: {lora_base}")
    
    if lora_exists:
        checks_passed += 1
        
        # Check individual style folders
        styles = ['bandhani', 'batik', 'ikat']
        for style in styles:
            checks_total += 1
            style_dir = lora_base / f"{style}_lora"
            adapter_config = style_dir / "adapter_config.json"
            adapter_model = style_dir / "adapter_model.safetensors"
            
            style_ok = (
                style_dir.exists() and
                adapter_config.exists() and
                adapter_model.exists()
            )
            
            print(f"  {check_mark(style_ok)} {style}_lora/")
            if style_ok:
                checks_passed += 1
                size_mb = adapter_model.stat().st_size / (1024 * 1024)
                print(f"      adapter_model.safetensors ({size_mb:.1f} MB)")
            else:
                issues.append(f"Missing or incomplete {style}_lora folder")
    else:
        issues.append(f"LoRA directory not found at: {lora_base}")
    
    # 5. Check backend files
    print()
    print("Checking backend files:")
    
    required_files = [
        'app/utils/lora_generator.py',
        'app/routes/generation.py',
        'config.py',
        'requirements.txt'
    ]
    
    for file in required_files:
        checks_total += 1
        filepath = backend_dir / file
        exists = filepath.exists()
        print(f"  {check_mark(exists)} {file}")
        if exists:
            checks_passed += 1
        else:
            issues.append(f"Missing file: {file}")
    
    # 6. Check uploads directory
    print()
    checks_total += 1
    uploads_dir = backend_dir / "uploads"
    uploads_exists = uploads_dir.exists()
    
    if not uploads_exists:
        try:
            uploads_dir.mkdir(parents=True, exist_ok=True)
            uploads_exists = True
            print(f"✅ uploads/ directory: Created")
        except:
            print(f"❌ uploads/ directory: Failed to create")
            issues.append("Cannot create uploads directory")
    else:
        print(f"✅ uploads/ directory: Exists")
    
    if uploads_exists:
        checks_passed += 1
    
    # Summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nChecks passed: {checks_passed}/{checks_total}")
    
    if checks_passed == checks_total:
        print("\n✅ ALL CHECKS PASSED! Ready to start backend.")
        print("\nNext steps:")
        print("  1. Run: python app.py")
        print("  2. Or test: python test_lora_generator.py")
        print("  3. Or batch: test_lora.bat")
        return True
    else:
        print(f"\n⚠️  {checks_total - checks_passed} issue(s) found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\nRecommended actions:")
        if any('pip install' in issue for issue in issues):
            print("  - Install missing packages: pip install -r requirements.txt")
        if any('LoRA' in issue for issue in issues):
            print("  - Verify textile_loras_trained folder is in parent directory")
        
        return False

if __name__ == "__main__":
    success = verify_setup()
    print()
    
    if success:
        sys.exit(0)
    else:
        input("Press Enter to exit...")
        sys.exit(1)
