import boto3
from PIL import Image, ImageDraw, ImageFont

# Initialize the boto3 client for S3 and Rekognition
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

def get_image_labels(bucket, key, confidence_threshold=90):
    # Detect labels in the image using Amazon Rekognition
    response = rekognition_client.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MinConfidence=confidence_threshold
    )
    print("Labels detected:", response['Labels']) 
    return response['Labels']

def download_image(bucket, key, download_path):
    # Download the image from S3
    s3_client.download_file(bucket, key, download_path)

def draw_bounding_boxes(image_path, labels):
    # Open the image file
    with Image.open(image_path) as img:
        # Convert image to RGB if it has an alpha channel
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        font_size = 16
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()  
        
        print(f"Image size: {img.size}")  
        
        # Draw bounding boxes for each detected label
        for label in labels:
            for instance in label.get('Instances', []):
                box = instance['BoundingBox']
                width, height = img.size
                left = width * box['Left']
                top = height * box['Top']
                right = left + (width * box['Width'])
                bottom = top + (height * box['Height'])

                print(f"Drawing box: {left, top, right, bottom}")  
                draw.rectangle([left, top, right, bottom], outline='red', width=5)  
                
                # Create text with background
                text = f"{label['Name']} ({instance['Confidence']:.2f}%)"
                text_bbox = draw.textbbox((left, top), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_background = (left, top - text_height, left + text_width, top)
                
                # Draw the semi-transparent white background
                draw.rectangle(text_background, fill=(255, 255, 255, 128))
                
                # Draw the border for the background
                draw.rectangle(text_background, outline='black', width=2)  
                
                # Draw the text
                draw.text((left, top - text_height), text, fill='red', font=font)
        
        # Save the image with bounding boxes
        img.save(image_path)

def process_images(bucket_name, image_keys):
    for image_key in image_keys:
        download_path = 'downloaded_' + image_key
        # Download the image from S3
        download_image(bucket_name, image_key, download_path)
        
        # Get labels from Amazon Rekognition
        labels = get_image_labels(bucket_name, image_key)
        
        # Draw bounding boxes on the image
        draw_bounding_boxes(download_path, labels)

def main():
    bucket_name = 'image-label-generator'
    image_keys_input = input("Enter the image names separated by commas: ")
    image_keys = [key.strip() for key in image_keys_input.split(',')]
    
    process_images(bucket_name, image_keys)

if __name__ == '__main__':
    main()
