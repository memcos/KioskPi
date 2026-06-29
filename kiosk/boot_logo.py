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

def apply_boot_mode(mode):
    script_path = "/usr/share/plymouth/themes/kioskpi/kioskpi.script"
    
    script_image_only = """
Window.SetBackgroundTopColor (0, 0, 0);
Window.SetBackgroundBottomColor (0, 0, 0);
logo_image = Image("logo.png");
screen_width = Window.GetWidth();
screen_height = Window.GetHeight();
logo_width = logo_image.GetWidth();
logo_height = logo_image.GetHeight();
x = (screen_width - logo_width) / 2;
y = (screen_height - logo_height) / 2;
logo_sprite = Sprite(logo_image);
logo_sprite.SetPosition(x, y, 0);
"""

    script_image_and_log = script_image_only + """
message_sprite = Sprite();
fun message_callback (text) {
  my_image = Image.Text(text, 1, 1, 1);
  message_sprite.SetImage(my_image);
  message_sprite.SetPosition((Window.GetWidth() - my_image.GetWidth()) / 2, y + logo_height + 40, 10000);
}
Plymouth.SetUpdateStatusFunction (message_callback);
"""

    script_text_only = """
Window.SetBackgroundTopColor (0, 0, 0);
Window.SetBackgroundBottomColor (0, 0, 0);
message_sprite = Sprite();
fun message_callback (text) {
  my_image = Image.Text(text, 1, 1, 1);
  message_sprite.SetImage(my_image);
  message_sprite.SetPosition((Window.GetWidth() - my_image.GetWidth()) / 2, (Window.GetHeight() - my_image.GetHeight()) / 2, 10000);
}
Plymouth.SetUpdateStatusFunction (message_callback);
"""

    if mode == "text_only":
        content = script_text_only
    elif mode == "image_and_log":
        content = script_image_and_log
    else:
        content = script_image_only

    try:
        if not os.path.exists("/usr/share/plymouth/themes/kioskpi"):
            return False
            
        with open(script_path, "w") as f:
            f.write(content)
        
        # Stop display to save RAM during initramfs rebuild
        subprocess.run(["systemctl", "stop", "greetd"], check=False)
        
        # Rebuild initramfs
        subprocess.run(["plymouth-set-default-theme", "-R", "kioskpi"], check=True)
        
        # Restart display
        subprocess.run(["systemctl", "start", "greetd"], check=False)
        
        return True
    except Exception as e:
        print(f"Error applying boot mode: {e}")
        subprocess.run(["systemctl", "start", "greetd"], check=False)
        return False
