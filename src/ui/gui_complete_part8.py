        elif cipher_type == 'p':  # Polyalphabetic cipher
            self.analysis_result.insert(tk.END, "Analyzing with Polyalphabetic cipher techniques...\n\n")
            results = self.cipher_service.analyze_polyalphabetic_encryption(text)
            
            if not results:
                self.analysis_result.insert(tk.END, "No results found. Try a different cipher type.")
                return
                
            # Store results for later use
            self.analysis_results = results
            
            # Display results
            for i, result in enumerate(results):
                self.analysis_result.insert(
                    tk.END, 
                    f"Suggestion {i+1}: Keyword = '{result['keyword']}' "
                    f"(Confidence: {result['confidence']}%)\n"
                )
                self.analysis_result.insert(tk.END, f"Sample: {result['sample']}\n\n")
                
            # Enable the apply button
            self.apply_button.config(state=tk.NORMAL)
            
        else:
            self.analysis_result.insert(
                tk.END, 
                f"AI analysis is currently only available for Caesar and "
                f"Polyalphabetic ciphers.\n\n"
                f"Please select one of these cipher types and try again."
            )

    def _apply_suggested_key(self):
        """
        Apply the selected key from the analysis results.
        
        This method takes the first (highest confidence) result from the
        analysis and applies it to the appropriate key field.
        """
        if not self.analysis_results:
            return
            
        # Get the selected cipher type
        cipher_type = self.cipher_var.get()
        
        # Get the highest confidence result
        result = self.analysis_results[0]
        
        if cipher_type == 'c':  # Caesar cipher
            # Set the shift value
            self.caesar_key_entry.delete(0, tk.END)
            self.caesar_key_entry.insert(0, str(result['shift']))
            
        elif cipher_type == 'p':  # Polyalphabetic cipher
            # Set the keyword
            self.poly_key_entry.delete(0, tk.END)
            self.poly_key_entry.insert(0, result['keyword'])
            
        # Set action to decrypt
        self.action_var.set('d')
        
        # Show a message
        messagebox.showinfo(
            "Key Applied", 
            "The suggested key has been applied. Click 'Process' to decrypt."
        )


def main():
    """Main function to start the GUI application."""
    root = tk.Tk()
    app = CipherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()