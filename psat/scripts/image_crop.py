import os
import cv2
import numpy as np


def remove_margins(image, margin=30) -> np.ndarray:
    """Remove white margins from the image."""
    # Find the topmost, bottommost, leftmost, and rightmost non-white pixels
    top = None
    bottom = None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # Iterate over the image pixels from top to bottom
    for y in range(binary.shape[0]):
        if top is not None and bottom is not None:
            break

        # Check if the topmost pixel is found
        if top is None:
            if np.any(binary[y, :] != 255):
                top = y

        # Check if the bottommost pixel is found
        if bottom is None:
            y_rev = binary.shape[0] - 1 - y
            if np.any(binary[y_rev, :] != 255):
                bottom = binary.shape[0] - 1 - y

    # Add or subtract the margin value from the boundary points
    top -= margin
    bottom += margin

    # Ensure the boundary points are within the image bounds
    top = max(0, top)
    bottom = min(binary.shape[0] - 1, bottom)

    return image[top:bottom + 1]


def find_split_point(image):
    height = image.shape[0]

    if height <= 1000:
        return height, None
    else:
        split_point = height // 2  # 이미지 높이의 절반을 기준으로 설정

        # 이미지의 높이가 절반 이상인 지점부터 아래로 흰색 픽셀 여부 확인
        for i in range(split_point, height):
            if np.all(image[i, :] == 255):  # 흰색 픽셀로만 이루어진 경우
                return i+5, image[i+6:, :]

        # 흰색 픽셀로만 이루어진 부분이 없을 경우 이미지의 높이를 그대로 반환
        return height, None


def process_images_in_folder(input_folder, output_folder):
    for file in os.listdir(input_folder):
        file_name, file_ext = os.path.splitext(file)
        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            file_path = os.path.join(input_folder, file)

            # 파일명의 인코딩을 UTF-8로 지정하여 파일을 읽음
            image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

            if image is not None:
                image_without_margin = remove_margins(image)
                split_point, second_image = find_split_point(image_without_margin)

                first_image = image_without_margin[:split_point, :]
                output_file_name = f'{file_name}-1{file_ext}'
                output_file_path = os.path.join(output_folder, output_file_name)
                cv2.imencode(file_ext, first_image)[1].tofile(output_file_path)

                if second_image is not None:
                    output_file_name = f'{file_name}-2{file_ext}'
                    output_file_path = os.path.join(output_folder, output_file_name)
                    cv2.imencode(file_ext, second_image)[1].tofile(output_file_path)


def run():
    module_folder = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(module_folder, 'input')
    output_folder = os.path.join(module_folder, 'output')
    process_images_in_folder(input_folder, output_folder)
