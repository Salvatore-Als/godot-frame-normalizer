import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class SpriteSheetEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sprite Sheet Editor")
        
        self.image_path = None
        self.image = None
        self.sprites = []
        self.sprite_height = 64
        self.num_columns = 8
        self.num_rows = 1
        self.column_positions = [self.sprite_height * i for i in range(self.num_columns)]
        self.dragging_col = None
        self.original_image = None
        self.max_sprite_width = 0
        self.width = 800

        self.load_button = tk.Button(self, text="Load SpriteSheet", command=self.load_image)
        self.load_button.pack()

        self.num_columns_label = tk.Label(self, text="Number of Columns:")
        self.num_columns_label.pack()
        self.num_columns_entry = tk.Entry(self)
        self.num_columns_entry.insert(0, str(self.num_columns))
        self.num_columns_entry.pack()

        self.num_rows_label = tk.Label(self, text="Number of Rows:")
        self.num_rows_label.pack()
        self.num_rows_entry = tk.Entry(self)
        self.num_rows_entry.insert(0, str(self.num_rows))
        self.num_rows_entry.pack()

        self.sprite_size_label = tk.Label(self, text="Sprite Size (Height):")
        self.sprite_size_label.pack()
        self.sprite_size_entry = tk.Entry(self)
        self.sprite_size_entry.insert(0, str(self.sprite_height))
        self.sprite_size_entry.pack()

        self.display_button = tk.Button(self, text="Display Grid", command=self.display_grid)
        self.display_button.pack()
        
        self.process_button = tk.Button(self, text="Process", command=self.process_and_display)
        self.process_button.pack()

        self.process_button = tk.Button(self, text="Export", command=self.export)
        self.process_button.pack()

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack()

        self.canvas = tk.Canvas(self.canvas_frame, width=self.width, height=500)
        self.canvas.grid(row=0, column=0)

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path = file_path
            self.image = Image.open(self.image_path)
            self.original_image = self.add_margin(self.image.copy(), 20, (0, 0, 0, 0))
            self.process_sprites()
            self.display_grid()

    def add_margin(self, pil_img, size, color):
        width, height = pil_img.size
        new_width = width + size + size
        result = Image.new(pil_img.mode, (new_width, height), color)
        result.paste(pil_img, (size, 0))

        return result

    def process_sprites(self):
        self.sprites = []
        sprite_height = int(self.sprite_size_entry.get())
        sprite_width = sprite_height  # Assumption: sprite is square
        num_columns = int(self.num_columns_entry.get())
        num_rows = int(self.num_rows_entry.get())

        sprite_x = self.image.width // sprite_width
        sprite_y = self.image.height // sprite_height

        for y in range(sprite_y):
            row_sprites = []
            for x in range(sprite_x):
                sprite = self.image.crop((x * sprite_width, y * sprite_height, (x + 1) * sprite_width, (y + 1) * sprite_height))
                
                # Recalc sprite size to have desired size
                sprite = sprite.resize((sprite_width, sprite_height))
                row_sprites.append(sprite)
            self.sprites.append(row_sprites)

    def process_and_display(self):
        try:
            # Original image display as first
            self.display_grid()
            
            # Create process image after original
            processed_image = self.create_processed_image()

            # Tkinter conversion
            processed_photo = ImageTk.PhotoImage(processed_image)
            
            # Calculate y position of the original image
            original_height = self.original_image.height
            
            # Display process image
            self.canvas.create_image(0, original_height + 50, anchor=tk.NW, image=processed_photo)
            self.canvas.processed_image = processed_photo
            
        except Exception as e:
            print(f"Unable to process: {e}")

    def crop_transparent_borders(self, image):
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        bbox = image.getbbox()
        border = self.sprite_height / 2
    
        if bbox:
            left, top, right, bottom = bbox
            
            left = max(left - border, 0)
            right = min(right + border, image.width)

            # Recadrer l'image pour qu'elle ait 32px de transparence à gauche et à droite
            image = image.crop((left, top, right, bottom))

        return image
        
    def find_sprite_in_section(self, start_x, end_x, row, sprite_height):
        """
        Find the sprite limit in a section by checking the colored pixels
        """
        section = self.original_image.crop((start_x, row * sprite_height, end_x, (row + 1) * sprite_height))
        
        # RGBA convertion 
        if section.mode != 'RGBA':
            section = section.convert('RGBA')
        
        # Pixel data
        data = section.getdata()
        width, height = section.size

        # Found the first pixel that is not transparency (start of sprite)
        sprite_start = self.find_pixel(range(width), section, 0)

        # Found the last pixel that is not transparency (end of sprite)
        sprite_end = self.find_pixel(range(width-1, -1, -1), section, 1)
                
        if sprite_start is None or sprite_end is None:
            return None
            
        # Extract sprite
        sprite = section.crop((sprite_start, 0, sprite_end, height))
        sprite_width = sprite_end - sprite_start

        return sprite, sprite_start, sprite_width

    def find_pixel(self, rrange, section, offset):
        value = None 

        data = section.getdata()
        width, height = section.size

        for x in rrange:
            for y in range(height):
                pixel = data[y * width + x]
                if pixel[3] > 0:  # Pixel not transparency
                    value = x + offset
                    break
            if value is not None:
                break
        
        return value

    def find_max_sprite_width(self):
        """
        Found the maximal sprite witdh
        """
        sprite_height = int(self.sprite_size_entry.get())
        num_rows = int(self.num_rows_entry.get())
        max_width = 0

        sorted_positions = sorted(self.column_positions)
        positions = [0] + sorted_positions + [self.original_image.width]

        for row in range(num_rows):
            for i in range(len(positions) - 1):
                start_pos = positions[i]
                end_pos = positions[i + 1]
                
                result = self.find_sprite_in_section(int(start_pos), int(end_pos), row, sprite_height)
                if result is not None:
                    _, _, sprite_width = result
                    max_width = max(max_width, sprite_width)

        # Add margin (64 px as default)
        requested_size = int(self.sprite_size_entry.get())
        if max_width < requested_size:
            max_width = requested_size
            
        return max_width

    def create_processed_image(self):
        sprite_height = int(self.sprite_size_entry.get())
        sprite_width = sprite_height  # Assumption: sprite is square
        num_rows = int(self.num_rows_entry.get())
        
        # Find max width of sprite 
        self.max_sprite_width = self.find_max_sprite_width()
        
        # Calculate new max width total of the img
        sorted_positions = sorted(self.column_positions)
        num_sections = len(sorted_positions) + 1
        new_width = self.max_sprite_width * num_sections
        new_height = self.original_image.height
        
        processed_image = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
        
        # Treatment position
        positions = [0] + sorted_positions + [self.original_image.width]
        
        for row in range(num_rows):
            # Each section between 2 red line
            for i in range(len(positions) - 1):
                start_pos = positions[i]
                end_pos = positions[i + 1]
                
                # Find the sprite in the section
                result = self.find_sprite_in_section(int(start_pos), int(end_pos), row, sprite_height)
                if result is not None:
                    sprite, _, sprite_width = result
                    
                    # Resize sprite to match the fixed dimensions (sprite_width, sprite_height)
                    sprite = sprite.resize((sprite_width, sprite_height))
                    
                    # Calculate position on the new image
                    new_section_start = i * self.max_sprite_width
                    margin = (self.max_sprite_width - sprite_width) // 2
                    sprite_x = new_section_start + margin
                    
                    # Set the sprite at calculated position
                    processed_image.paste(sprite, (int(sprite_x), row * sprite_height))
        
        processed_image = self.crop_transparent_borders(processed_image)
        return processed_image

    def resize_from_window_size(self, image):
        window_width = self.winfo_width()

        # Ratio
        original_width, original_height = image.size
        ratio = original_height / original_width

        new_width = window_width
        new_height = int(window_width * ratio)

        resized_image = image.resize((new_width, new_height))
        return resized_image

    def display_grid(self):
        try:
            self.sprite_height = int(self.sprite_size_entry.get())
            self.num_columns = int(self.num_columns_entry.get())
            self.num_rows = int(self.num_rows_entry.get())

            if len(self.column_positions) != self.num_columns:
                self.column_positions = [self.sprite_height * i for i in range(self.num_columns)]

            # Clean all
            self.canvas.delete("all")

            # Display original image
            if self.original_image:
                #resized_image = self.resize_from_window_size(self.original_image)
              
                photo = ImageTk.PhotoImage(self.original_image)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.canvas.original_image = photo
                
            # Draw red line
            self.draw_grid_borders()

        except ValueError:
            print("Veuillez entrer des valeurs valides.")

    def draw_grid_borders(self):
        # Draw draggable red line
        for col in range(self.num_columns):
            x = self.column_positions[col]
            self.canvas.create_line(x, 0, x, self.sprite_height * self.num_rows,
                                  fill="red", width=1, tags=f"drag_bar_{col}")
            self.canvas.tag_bind(f"drag_bar_{col}", "<Button-1>",
                               lambda event, col=col: self.start_drag(event, col))
            self.canvas.tag_bind(f"drag_bar_{col}", "<B1-Motion>",
                               lambda event, col=col: self.dragging(event, col))
            self.canvas.tag_bind(f"drag_bar_{col}", "<ButtonRelease-1>", self.stop_drag)

    def start_drag(self, event, col):
        self.dragging_col = col

    def dragging(self, event, col):
        if self.dragging_col is not None:
            new_position = event.x
            if new_position >= 0:
                self.canvas.coords(f"drag_bar_{self.dragging_col}",
                                 new_position, 0, new_position,
                                 self.sprite_height * self.num_rows)
                self.column_positions[self.dragging_col] = new_position

    def stop_drag(self, event):
        self.dragging_col = None

    def export(self):
        processed_image = self.create_processed_image()
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        
        if file_path:
            processed_image.save(file_path)

    
if __name__ == "__main__":
    app = SpriteSheetEditor()
    app.mainloop()