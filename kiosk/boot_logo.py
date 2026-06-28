import os
import subprocess
import shutil

def apply_logo(image_path):
    """
    Sets up the plymouth boot theme with the uploaded image.
    Requires root privileges via sudo (must be configured in sudoers or script runs as root)
    """
    theme_name = "kioskpi"
    theme_dir = f"/usr/share/plymouth/themes/{theme_name}"
    
    try:
        # Check if theme exists in system, if not create it from local skeleton
        if not os.path.exists(theme_dir):
            subprocess.run(f"sudo mkdir -p {theme_dir}", shell=True, check=True)
            subprocess.run(f"sudo cp -r /opt/kioskpi/plymouth/{theme_name}/* {theme_dir}/", shell=True, check=True)
            
        # Copy the new image as logo.png
        ext = image_path.rsplit('.', 1)[1].lower()
        if ext in ['jpg', 'jpeg']:
            # Plymouth prefers png, try to use imagemagick or just rename and hope the renderer accepts it
            # To be safe, we just copy it as logo.png (plymouth two-step plugin supports jpg/png)
            pass
            
        subprocess.run(f"sudo cp {image_path} {theme_dir}/logo.png", shell=True, check=True)
        
        # Make sure it's the default theme
        subprocess.run(f"sudo plymouth-set-default-theme -R {theme_name}", shell=True, check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error applying boot logo: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
