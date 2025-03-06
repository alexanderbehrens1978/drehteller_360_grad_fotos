import os
import random
import math
from PIL import Image, ImageDraw, ImageFont


class SampleImagesGenerator:
    def __init__(self, output_path='static/sample_images', width=800, height=600):
        """
        Generate sample images for webcam simulator

        :param output_path: Directory to save generated images
        :param width: Image width
        :param height: Image height
        """
        self.output_path = output_path
        self.width = width
        self.height = height

        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

    def generate_color_gradient_image(self, index):
        """
        Generate an image with a color gradient

        :param index: Unique identifier for the image
        :return: Path to the generated image
        """
        # Create a new image with a gradient
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        # Generate gradient colors
        for y in range(self.height):
            r = int(255 * y / self.height)
            g = int(255 * (1 - y / self.height))
            b = int(128 + 127 * math.sin(y / 50))

            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Add text to identify the image
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except IOError:
            font = ImageFont.load_default()

        draw.text((50, 50), f"Sample Image {index}", font=font, fill=(255, 255, 255))

        # Save the image
        filename = os.path.join(self.output_path, f'sample_image_{index}.jpg')
        image.save(filename)
        return filename

    def generate_sample_images(self, count=10):
        """
        Generate multiple sample images

        :param count: Number of images to generate
        :return: List of generated image paths
        """
        generated_images = []
        for i in range(count):
            image_path = self.generate_color_gradient_image(i)
            generated_images.append(image_path)

        return generated_images


# Optionally, if you want to use this as a standalone script
if __name__ == '__main__':
    generator = SampleImagesGenerator()
    generated_images = generator.generate_sample_images()

    print("Generated Sample Images:")
    for img in generated_images:
        print(img)
