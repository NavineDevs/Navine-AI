class SiteAPI:
    def get_settings(self):
        # Implement the get_settings method to retrieve the settings for the website
        # Example implementation:
        return {
            'output_folder': '/path/to/output/folder'
            # Other settings...
        }

    def mdtohtml(self, markdown_content):
        # Implement the mdtohtml method to convert Markdown content to HTML
        # Example implementation:
        # (Assuming a markdown to HTML conversion library is used)
        import markdown
        html_content = markdown.markdown(markdown_content)
        return html_content

    def create_file(self, info, file_name, file_path, **kwargs):
        # Implement the create_file method to create a new file in the specified output folder
        # Example implementation:
        with open(file_path, 'w') as file:
            file.write('<html><body>')
            file.write(kwargs['core_basics'])  # Incorporate the provided content
            file.write('</body></html>')
        # Additional file creation logic as per requirements
