import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import json

class MazeDesigner(tk.Tk):
    def __init__(self, grid_rows, grid_cols):
        super().__init__()
        self.title("Maze Designer")
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.cell_size = 40
        self.canvas_width = grid_cols * self.cell_size
        self.canvas_height = grid_rows * self.cell_size
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()

        self.grid_data = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)] # Initialize with all walls

        self.start_cell = None       # Track starting cell for left-click dragging
        self.start_cell_right = None # Ditto but for right click

        self.start_pos = None        # (row, col) of the start position
        self.end_pos = None          # (row, col) of the end position
        self.fruit_positions = set() # Set of (row, col) tuples for fruits

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.canvas.bind("<ButtonPress-3>", self.on_mouse_down_right)
        self.canvas.bind("<B3-Motion>", self.on_mouse_drag_right)
        self.canvas.bind("<ButtonRelease-3>", self.on_mouse_up_right)

        self.bind("<Key>", self.on_key_press)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        export_button = tk.Button(button_frame, text="Export to JSON", command=self.export_to_json)
        export_button.pack(side=tk.LEFT, padx=5)

        load_button = tk.Button(button_frame, text="Load Maze", command=self.load_maze)
        load_button.pack(side=tk.LEFT, padx=5)

        reset_button = tk.Button(button_frame, text="Reset Maze", command=self.reset_maze)
        reset_button.pack(side=tk.LEFT, padx=5)

        self.draw_grid()
    
    def draw_grid(self):
        self.canvas.delete("all") # Clear the canvas
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = (c + 1) * self.cell_size
                y2 = (r + 1) * self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="lightgray") # Draw cell boundaries
                self.draw_walls(r, c, self.grid_data[r][c])
                self.draw_special_elements(r, c, x1, y1, x2, y2)

    def draw_special_elements(self, row, col, x1, y1, x2, y2):
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        if self.start_pos == (row, col):
            self.canvas.create_text(center_x, center_y, text="S", font=("Arial", 16, "bold"), fill="green")
        if self.end_pos == (row, col):
            self.canvas.create_text(center_x, center_y, text="E", font=("Arial", 16, "bold"), fill="red")
        if (row, col) in self.fruit_positions:
            self.canvas.create_oval(center_x - 8, center_y - 8, center_x + 8, center_y + 8, fill="yellow", outline="orange")

    
    def draw_walls(self, row, col, cell_value):
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = (col + 1) * self.cell_size
        y2 = (row + 1) * self.cell_size

        # Binary representation of cell value(left, down, right, up)
        binary_value = bin(cell_value)[2:].zfill(4)

        if binary_value[0] == '0': # Left wall present
            self.canvas.create_line(x1, y1, x1, y2, width=2)
        if binary_value[1] == '0': # Down wall present
            self.canvas.create_line(x1, y2, x2, y2, width=2)
        if binary_value[2] == '0': # Right wall present
            self.canvas.create_line(x2, y1, x2, y2, width=2)
        if binary_value[3] == '0': # Up wall present
            self.canvas.create_line(x1, y1, x2, y1, width=2)

    def get_cell_coords(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        return row, col
    
    def on_mouse_down(self, event):
        self.start_cell = self.get_cell_coords(event)
        self.start_cell_right = None # Ensure no right-clicking

    def on_mouse_drag(self, event):
        if self.start_cell:
            end_cell = self.get_cell_coords(event)
            start_row, start_col = self.start_cell
            end_row, end_col = end_cell

            if (0 <= end_row < self.grid_rows and 0 <= end_col < self.grid_cols and
                (abs(start_row - end_row) + abs(start_col - end_col) == 1)): # Only adjacent cells

                direction = self.get_neighbor_direction(start_row, start_col, end_row, end_col)
                if direction is not None:
                    # Upgrade grid data
                    self.remove_wall_between_cells(start_row, start_col, end_row, end_col, direction)
                    self.start_cell = end_cell # Allow continuous dragging
                    self.draw_grid() # Redraw the grid after removing a wall
                    
    
    def on_mouse_up(self, event):
        self.start_cell = None

    def on_mouse_down_right(self, event):
        self.start_cell_right = self.get_cell_coords(event)
        self.start_cell = None # Ensure no left-click drag is active        

    def on_mouse_drag_right(self, event):
        if self.start_cell_right:
            end_cell = self.get_cell_coords(event)
            start_row, start_col = self.start_cell_right
            end_row, end_col = end_cell

            if (0 <= end_row < self.grid_rows and 0 <= end_col < self.grid_cols and
                    (abs(start_row - end_row) + abs(start_col - end_col) == 1)): # Only adjacent cells

                direction = self.get_neighbor_direction(start_row, start_col, end_row, end_col)
                if direction is not None:
                    self.add_wall_between_cells(start_row, start_col, end_row, end_col, direction)
                    self.start_cell_right = end_cell # Allow continuous dragging
                    self.draw_grid() # Redraw the grid after adding a wall

    def on_mouse_up_right(self, event):
        self.start_cell_right = None

    def on_key_press(self, event):
        canvas_x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()

        # Create a dummy event object with canvas_x and canvas_y
        class DummyEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        dummy_event = DummyEvent(canvas_x, canvas_y)
        row, col = self.get_cell_coords(dummy_event)

        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            if event.keysym.upper() == 'S':
                self.start_pos = (row, col)
                self.draw_grid()
            elif event.keysym.upper() == 'E':
                self.end_pos = (row, col)
                self.draw_grid()
            elif event.keysym.upper() == 'F':
                if (row, col) in self.fruit_positions:
                    self.fruit_positions.remove((row, col))
                else:
                    self.fruit_positions.add((row, col))
                self.draw_grid()

    
    def get_neighbor_direction(self, start_row, start_col, end_row, end_col):
        if end_col < start_col:
            return 0  # Left
        elif end_row > start_row:
            return 1  # Down
        elif end_col > start_col:
            return 2  # Right
        elif end_row < start_row:
            return 3  # Up
        return None
    
    def remove_wall_between_cells(self, r1, c1, r2, c2, direction):
        # Update starting cell
        if direction == 0:  # Moving Left from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] | 0b1000  # Remove left wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] | 0b0010  # Remove right wall of the neighbor
        elif direction == 1:  # Moving Down from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] | 0b0100  # Remove down wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] | 0b0001  # Remove up wall of the neighbor
        elif direction == 2:  # Moving Right from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] | 0b0010  # Remove right wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] | 0b1000  # Remove left wall of the neighbor
        elif direction == 3:  # Moving Up from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] | 0b0001  # Remove up wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] | 0b0100  # Remove down wall of the neighbor

    def add_wall_between_cells(self, r1, c1, r2, c2, direction):
        if direction == 0:  # Moving Left from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] & ~0b1000  # Add left wall (set bit to 0)
            self.grid_data[r2][c2] = self.grid_data[r2][c2] & ~0b0010  # Add right wall of neighbor
        elif direction == 1:  # Moving Down from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] & ~0b0100  # Add down wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] & ~0b0001  # Add up wall of neighbor
        elif direction == 2:  # Moving Right from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] & ~0b0010  # Add right wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] & ~0b1000  # Add left wall of neighbor
        elif direction == 3:  # Moving Up from (r1, c1) to (r2, c2)
            self.grid_data[r1][c1] = self.grid_data[r1][c1] & ~0b0001  # Add up wall
            self.grid_data[r2][c2] = self.grid_data[r2][c2] & ~0b0100  # Add down wall of neighbor

    def get_hex_string(self):
        hex_string = ""
        for row in self.grid_data:
            for cell_value in row:
                hex_string += hex(cell_value)[2:].upper()
        return hex_string
    
    def export_to_json(self):
        # level_name = simpledialog.askstring("Export", "Enter Level Name:", parent=self)

        # if level_name is None:
        #     return # User cancelled
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Maze JSON File"
        )

        if not file_path:
            return
        
        maze_data = {
            "seed": self.get_hex_string(),
            "levelStart": None,
            "levelEnd": None,
            "fruits": {}
        }

        if self.start_pos:
            maze_data["levelStart"] = {"x": self.start_pos[1] + 1, "y": self.start_pos[0] + 1}
        if self.end_pos:
            maze_data["levelEnd"] = {"x": self.end_pos[1] + 1, "y": self.end_pos[0] + 1}
        
        for i, (row, col) in enumerate(sorted(list(self.fruit_positions))):
            maze_data["fruits"][f"fr{i+1}"] = {"x": col + 1, "y": row + 1}

        try:
            with open(file_path, 'w') as f:
                json.dump(maze_data, f, indent=4)
            messagebox.showinfo("Export Successful", f"Maze data exported to '{file_path}'")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export: {e}")
    
    def load_maze(self):

        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*")],
            title="Open Maze JSON File"
        )

        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)

            # Reset current maze
            self.grid_data = [[0 for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
            self.start_pos = None
            self.end_pos = None
            self.fruit_positions = set()

            # Load hex string back into grid_data
            hex_string = loaded_data.get("seed", "")
            if len(hex_string) != self.grid_rows * self.grid_cols:
                raise ValueError("Hex string length does not match expected grid size.")

            cell_idx = 0
            for r in range(self.grid_rows):
                for c in range(self.grid_cols):
                    hex_val = hex_string[cell_idx]
                    self.grid_data[r][c] = int(hex_val, 16)
                    cell_idx += 1
            
            # Load start position
            start_data = loaded_data.get("levelStart")
            if start_data and "x" in start_data and "y" in start_data:
                self.start_pos = (start_data["y"] - 1, start_data["x"] - 1)

            # Load end position
            end_data = loaded_data.get("levelEnd")
            if end_data and "x" in end_data and "y" in end_data:
                self.end_pos = (end_data["y"] - 1, end_data["x"] - 1)
            
            # Load fruits
            fruits_data = loaded_data.get("fruits", {})
            for fruit_key, fruit_coords in fruits_data.items():
                if "x" in fruit_coords and "y" in fruit_coords:
                    self.fruit_positions.add((fruit_coords["y"] - 1, fruit_coords["x"] - 1)) # (row, col)

            self.draw_grid() # Redraw the grid to show the loaded maze
            messagebox.showinfo("Load Successful", f"Maze loaded from '{file_path}'")

        except FileNotFoundError:
            messagebox.showerror("Load Error", "File not found.")
        except json.JSONDecodeError:
            messagebox.showerror("Load Error", "Invalid JSON file. Please ensure it's a valid maze JSON.")
        except ValueError as ve:
            messagebox.showerror("Load Error", f"Data format error: {ve}")
        except KeyError as ke:
            messagebox.showerror("Load Error", f"Missing key in JSON data: {ke}. Please check the file structure.")
        except Exception as e:
            messagebox.showerror("Load Error", f"An unexpected error occurred during load: {e}")

    def reset_maze(self):
        if messagebox.askyesno("Reset Maze", "Are you sure?"):
            self.grid_data = [[0 for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
            self.start_pos = None
            self.end_pos = None
            self.fruit_positions.clear()
            self.draw_grid()


if __name__ == "__main__":
    maze_app = MazeDesigner(9, 15)
    maze_app.focus_set()
    maze_app.mainloop()
