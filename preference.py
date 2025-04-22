import tkinter as tk
from tkinter import ttk, messagebox
import json
import csv
from datetime import datetime


class PreferenceCollector:
    def __init__(self, root):
        self.root = root
        self.root.title("Preference Data Collector")
        self.root.geometry("800x500")
        self.root.configure(padx=20, pady=20)

        # Set up data structure
        self.data_file = "preference_data.json"
        self.questions_file = "./data/questions.csv"
        self.current_index = 0
        self.questions = []
        self.responses = []

        # Load questions
        self.load_questions()

        # Load previous responses if they exist
        self.load_responses()

        # Set up UI components
        self.setup_ui()

        # Display first question or completion message
        self.display_current_question()

        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_questions(self):
        """Load questions from the CSV file"""
        try:
            with open(self.questions_file, "r", encoding="utf-8") as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    question = {
                        "sentence": row["translated"],
                        "option1": row["text"],
                        "option2": row["multi"],
                    }
                    self.questions.append(question)

                if not self.questions:
                    raise FileNotFoundError(
                        "CSV file was empty or improperly formatted"
                    )

        except FileNotFoundError:
            # Sample questions if file doesn't exist
            self.questions = [
                {
                    "sentence": "The movie was really enjoyable and entertaining.",
                    "option1": "I found the film to be quite delightful.",
                    "option2": "The cinematic experience gave me great pleasure.",
                },
                {
                    "sentence": "The company announced record profits this quarter.",
                    "option1": "The firm reported unprecedented earnings for this period.",
                    "option2": "The business revealed they had their most successful quarter yet.",
                },
                {
                    "sentence": "The researchers discovered a new species of frog.",
                    "option1": "Scientists identified a previously unknown amphibian of the frog family.",
                    "option2": "The research team found a type of frog that was not known before.",
                },
            ]
            # Create a sample CSV file
            with open(self.questions_file, "w", encoding="utf-8", newline="") as f:
                fieldnames = ["text", "multi", "translated"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for q in self.questions:
                    writer.writerow(
                        {
                            "text": q["option1"],
                            "multi": q["option2"],
                            "translated": q["sentence"],
                        }
                    )

    def load_responses(self):
        """Load previous responses if they exist and set the current index"""
        try:
            with open(self.data_file, "r") as f:
                self.responses = json.load(f)
                self.current_index = len(self.responses)
        except FileNotFoundError:
            self.responses = []
            self.current_index = 0

    def setup_ui(self):
        """Set up the user interface elements"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Original sentence frame
        sentence_frame = ttk.LabelFrame(main_frame, text="Original Sentence")
        sentence_frame.pack(fill=tk.X, padx=10, pady=10)

        self.sentence_label = ttk.Label(sentence_frame, text="", wraplength=750)
        self.sentence_label.pack(padx=10, pady=10)

        # Options frame
        options_frame = ttk.LabelFrame(
            main_frame, text="Which alternative do you prefer?"
        )
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        # Option selection
        self.option_var = tk.IntVar()

        self.option1_frame = ttk.Frame(options_frame)
        self.option1_frame.pack(fill=tk.X, padx=10, pady=5)

        self.option1_radio = ttk.Radiobutton(
            self.option1_frame, variable=self.option_var, value=1
        )
        self.option1_radio.pack(side=tk.LEFT, padx=5)

        self.option1_label = ttk.Label(self.option1_frame, text="", wraplength=700)
        self.option1_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.option2_frame = ttk.Frame(options_frame)
        self.option2_frame.pack(fill=tk.X, padx=10, pady=5)

        self.option2_radio = ttk.Radiobutton(
            self.option2_frame, variable=self.option_var, value=2
        )
        self.option2_radio.pack(side=tk.LEFT, padx=5)

        self.option2_label = ttk.Label(self.option2_frame, text="", wraplength=700)
        self.option2_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Confidence frame
        confidence_frame = ttk.LabelFrame(
            main_frame, text="How confident are you in your choice?"
        )
        confidence_frame.pack(fill=tk.X, padx=10, pady=10)

        self.confidence_var = tk.IntVar()
        self.confidence_var.set(3)  # Default middle value

        confidence_scale = ttk.Scale(
            confidence_frame,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.confidence_var,
            command=self.update_confidence_label,
        )
        confidence_scale.pack(fill=tk.X, padx=20, pady=5)

        confidence_labels_frame = ttk.Frame(confidence_frame)
        confidence_labels_frame.pack(fill=tk.X, padx=20)

        ttk.Label(confidence_labels_frame, text="Low").pack(side=tk.LEFT)
        self.confidence_value_label = ttk.Label(confidence_labels_frame, text="3")
        self.confidence_value_label.pack(side=tk.LEFT, expand=True)
        ttk.Label(confidence_labels_frame, text="High").pack(side=tk.RIGHT)

        # Navigation frame
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=20)

        self.progress_label = ttk.Label(nav_frame, text="")
        self.progress_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(nav_frame, text="Submit & Next", command=self.submit_response).pack(
            side=tk.RIGHT, padx=10
        )

    def update_confidence_label(self, event=None):
        """Update the confidence value label when the slider is moved"""
        value = int(self.confidence_var.get())
        self.confidence_value_label.config(text=str(value))

    def display_current_question(self):
        """Display the current question or show completion message if all questions answered"""
        if self.current_index >= len(self.questions):
            # All questions have been answered
            for widget in self.root.winfo_children():
                widget.destroy()

            completion_frame = ttk.Frame(self.root)
            completion_frame.pack(expand=True)

            ttk.Label(
                completion_frame,
                text="Thank you! All questions have been answered.",
                font=("Arial", 16),
            ).pack(pady=20)

            # Display summary
            total_responses = len(self.responses)
            ttk.Label(
                completion_frame, text=f"Total questions answered: {total_responses}"
            ).pack(pady=5)

            # Export data button
            ttk.Button(
                completion_frame, text="Export Results", command=self.export_results
            ).pack(pady=10)

            ttk.Button(completion_frame, text="Exit", command=self.root.destroy).pack(
                pady=10
            )

            return

        # Display current question
        question = self.questions[self.current_index]
        self.sentence_label.config(text=question["sentence"])
        self.option1_label.config(text=question["option1"])
        self.option2_label.config(text=question["option2"])

        # Reset option selection
        self.option_var.set(0)

        # Reset confidence to middle value
        self.confidence_var.set(3)
        self.update_confidence_label()

        # Update progress indicator
        self.progress_label.config(
            text=f"Question {self.current_index + 1} of {len(self.questions)}"
        )

    def submit_response(self):
        """Save the current response and move to the next question"""
        # Check if an option was selected
        if self.option_var.get() == 0:
            messagebox.showwarning(
                "Selection Required", "Please select an option before continuing."
            )
            return

        # Record the response
        question = self.questions[self.current_index]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        response = {
            "question_id": self.current_index,
            "sentence": question["sentence"],
            "selected_option": self.option_var.get(),
            "selected_text": (
                question["option1"]
                if self.option_var.get() == 1
                else question["option2"]
            ),
            "confidence": self.confidence_var.get(),
            "timestamp": timestamp,
        }

        # Add to responses list
        if self.current_index < len(self.responses):
            # Overwrite existing response (if resuming)
            self.responses[self.current_index] = response
        else:
            # Add new response
            self.responses.append(response)

        # Save responses to file
        self.save_responses()

        # Move to next question
        self.current_index += 1
        self.display_current_question()

    def save_responses(self):
        """Save responses to the data file"""
        with open(self.data_file, "w") as f:
            json.dump(self.responses, f, indent=4)

    def export_results(self):
        """Export results to a CSV file"""
        export_file = "preference_results.csv"
        try:
            with open(export_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "question_id",
                    "sentence",
                    "option1",
                    "option2",
                    "selected_option",
                    "selected_text",
                    "confidence",
                    "timestamp",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for i, response in enumerate(self.responses):
                    question = self.questions[response["question_id"]]
                    row = {
                        "question_id": response["question_id"],
                        "sentence": question["sentence"],
                        "option1": question["option1"],
                        "option2": question["option2"],
                        "selected_option": response["selected_option"],
                        "selected_text": response["selected_text"],
                        "confidence": response["confidence"],
                        "timestamp": response["timestamp"],
                    }
                    writer.writerow(row)

            messagebox.showinfo(
                "Export Successful", f"Results exported to {export_file}"
            )
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export results: {e}")

    def on_closing(self):
        """Handle window closing event"""
        if messagebox.askokcancel(
            "Quit", "Do you want to quit? Your progress will be saved."
        ):
            self.save_responses()
            self.root.destroy()


def main():
    root = tk.Tk()
    app = PreferenceCollector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
