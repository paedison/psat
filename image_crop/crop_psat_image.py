import os
import math
from multiprocessing import cpu_count, Pool

from pdf2image import convert_from_path
from PIL import Image, ImageChops
import openpyxl


def mm_to_pixels(mm, dpi):
    return math.ceil((mm / 25.4) * dpi)


def crop_with_margin(image, margin_mm=5, dpi=300):
    margin_px = mm_to_pixels(margin_mm, dpi)
    width, height = image.size
    return image.crop((
        margin_px,  # left
        margin_px,  # top
        width - margin_px,  # right
        height - margin_px  # bottom
    ))


def auto_crop_with_margin(img, margin_mm=5, dpi=300):
    # Convert to grayscale for more reliable bounding box detection
    gray = img.convert("L")
    bg = Image.new("L", img.size, 255)  # white background
    diff = ImageChops.difference(gray, bg)
    bbox = diff.getbbox()

    if not bbox:
        return img  # nothing to crop

    margin_px = mm_to_pixels(margin_mm, dpi)
    left = max(bbox[0] - margin_px, 0)
    top = max(bbox[1] - margin_px, 0)
    right = min(bbox[2] + margin_px, img.width)
    bottom = min(bbox[3] + margin_px, img.height)
    return img.crop((left, top, right, bottom))


def read_filenames_from_excel(excel_path):
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    return [str(row[0]) for row in ws.iter_rows(min_row=2, values_only=True) if row[0]]


def process_page(args):
    index, image, filename, margin_mm, dpi, output_dir = args
    try:
        output_path = os.path.join(output_dir, f"{filename}.png")
        if os.path.exists(output_path):
            print(f"[{index}] ⏭ Already exists: {output_path}")
            return
        cropped = auto_crop_with_margin(image, margin_mm, dpi)
        cropped.save(output_path, "PNG")
        print(f"[{index}] ✅ Saved: {output_path}")
    except Exception as e:
        print(f"[{index}] ❌ Error: {e}")


def convert_pdf_to_images(pdf_path, dpi, thread_count, first_page=None, last_page=None):
    return convert_from_path(
        pdf_path, dpi=dpi, thread_count=thread_count, first_page=first_page, last_page=last_page)


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default


def chunked(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield i, lst[i:i+chunk_size]


def main():
    print("=== PDF to JPEG Converter ===")
    pdf_path = get_user_input("Enter path to PDF file", "input.pdf", str)
    excel_path = get_user_input("Enter path to Excel file", "filenames.xlsx", str)
    output_dir = get_user_input("Enter output folder", "output_images", str)
    margin_mm = get_user_input("Enter margin in mm", 5, float)
    dpi = get_user_input("Enter resolution (DPI)", 300, int)
    thread_count = get_user_input("Enter thread count", cpu_count(), int)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filenames = read_filenames_from_excel(excel_path)
    total_pages = len(filenames)

    print(f"🔄 총 페이지 수: {total_pages} / 병렬 처리: {thread_count} threads")

    chunk_size = 30  # 한 번에 처리할 페이지 수
    for chunk_start, filename_chunk in chunked(filenames, chunk_size):
        first_page = chunk_start + 1
        last_page = chunk_start + len(filename_chunk)
        print(f"📄 처리 중: {first_page} ~ {last_page} 페이지...")

        images = convert_from_path(
            pdf_path=pdf_path,
            dpi=dpi,
            thread_count=thread_count,
            first_page=first_page,
            last_page=last_page,
        )

        task_list = [
            (chunk_start + idx + 1, img, filename_chunk[idx], margin_mm, dpi, output_dir)
            for idx, img in enumerate(images)
        ]

        with Pool(processes=thread_count) as pool:
            pool.map(process_page, task_list)

    print("🎉 모든 작업 완료!")


if __name__ == "__main__":
    main()
