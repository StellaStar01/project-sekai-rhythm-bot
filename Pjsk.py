import pyautogui
import time
import mss
import numpy as np


pyautogui.PAUSE = 0


pyautogui.FAILSAFE = False


HEIGHT_SCAN_START = 717
HEIGHT_SCAN_END = 721


BUTTON_X_RANGES = {
    'A': (330, 534),
    'S': (535, 736),
    'D': (737, 941),
    'F': (942, 1152),
    'G': (1153, 1359),
    'H': (1360, 1600)
}


CAPTURE_BBOX = (
    BUTTON_X_RANGES['A'][0],     # 330
    HEIGHT_SCAN_START,           # 717
    BUTTON_X_RANGES['H'][1] + 1, # 1600 + 1 = 1601
    HEIGHT_SCAN_END + 1          # 721 + 1 = 722
)


TAP_COLOR = (243, 243, 255)


SPECIAL_TAP_COLORS = {
    (255, 238, 246),  
    (255, 252, 204),  
    (252, 186, 217),  
}

SPECIAL_KEY_MAPPING = {
    'A': 'Q', 'S': 'W', 'D': 'E',
    'F': 'R', 'G': 'T', 'H': 'Y'
}


HOLD_COLOR_MIN = (40, 120, 120)
#HOLD_COLOR_MIN = (40, 120, 80)s
HOLD_COLOR_MAX = (255, 255, 255)

def perform_simultaneous_tap(keys_to_tap, message_prefix="Tapped buttons"):
    """Presses and releases a list of keys to simulate a simultaneous tap."""
    if not keys_to_tap:
        return

   
    tapped_keys_lower = [k.lower() for k in keys_to_tap]

    for k in tapped_keys_lower:
        pyautogui.keyDown(k)
    for k in tapped_keys_lower:
        pyautogui.keyUp(k)
    print(f"{message_prefix}: {', '.join(keys_to_tap)}")

def main():
    """Main function to run the rhythm game bot."""
    print("Bot is starting in 3 seconds. Switch to your game window.")
    time.sleep(3)
    print("Bot is running...")

    
    held_keys = set()

    
    relative_x_centers = {
        key: (x_start + x_end) // 2 - CAPTURE_BBOX[0]
        for key, (x_start, x_end) in BUTTON_X_RANGES.items()
    }

    
    special_colors_packed = np.array(
        [r << 16 | g << 8 | b for r, g, b in SPECIAL_TAP_COLORS], dtype=np.uint32)

    try:
        with mss.mss() as sct:
            while True:
                
                sct_img = sct.grab(CAPTURE_BBOX)
                
                
                screen_array = np.array(sct_img)
                screen_rgb = screen_array[:, :, :3][:, :, ::-1] 
                
              
                keys_to_hold_this_frame = set()
                keys_to_tap_this_frame = set()

                
                
                lane_keys = list(relative_x_centers.keys())
                x_coords = list(relative_x_centers.values())
                lanes_pixels = screen_rgb[:, x_coords]  

                
                tap_mask = np.all(lanes_pixels == TAP_COLOR, axis=2)

               
                lanes_pixels_packed = (lanes_pixels[..., 0].astype(np.uint32) << 16 |
                                       lanes_pixels[..., 1].astype(np.uint32) << 8 |
                                       lanes_pixels[..., 2].astype(np.uint32))
               
                special_tap_mask = np.isin(lanes_pixels_packed, special_colors_packed)

                
                hold_mask = np.all((lanes_pixels >= HOLD_COLOR_MIN) & (lanes_pixels <= HOLD_COLOR_MAX), axis=2)

                
                is_tap_in_lane = np.any(tap_mask, axis=0)
                is_special_tap_in_lane = np.any(special_tap_mask, axis=0)
                is_hold_in_lane = np.any(hold_mask, axis=0)

                
                for i, key in enumerate(lane_keys):
                    if is_special_tap_in_lane[i]:
                        keys_to_tap_this_frame.add(SPECIAL_KEY_MAPPING[key])
                    elif is_tap_in_lane[i]:
                        keys_to_tap_this_frame.add(key)
                    elif is_hold_in_lane[i]:
                        keys_to_hold_this_frame.add(key)

                
                
                
                perform_simultaneous_tap(list(keys_to_tap_this_frame), "Tapped notes")
                
                
                keys_to_press = keys_to_hold_this_frame - held_keys
                for key in keys_to_press:
                    pyautogui.keyDown(key.lower())
                    held_keys.add(key)
                    print(f"Holding down button {key}")

                keys_to_release = held_keys - keys_to_hold_this_frame
                for key in keys_to_release:
                    pyautogui.keyUp(key.lower())
                    held_keys.remove(key)
                    print(f"Released button {key}")

    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        
        for key in held_keys:
            pyautogui.keyUp(key.lower())
        print("All keys released.")

if __name__ == "__main__":
    main()