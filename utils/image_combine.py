from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

def combine_and_write(folder):
    try:
        folder.joinpath("results").mkdir()
    except FileExistsError:
        return
    
    result_folder = folder.joinpath("results")
    for rgb_img_path, segment_img_path in zip(folder.joinpath("rgb").glob("*"), folder.joinpath("segment").rglob("*")):

        with Image.open(rgb_img_path) as rgb_image, Image.open(segment_img_path) as segment_image:

            images = [rgb_image, segment_image]
            widths, heights = zip(*(i.size for i in images))

            new_im = Image.new('RGB', (sum(widths), max(heights)))

            x_offset = 0
            for im in images:
                new_im.paste(im, (x_offset, 0))
                x_offset += im.size[0]

            new_im.save(result_folder.joinpath(rgb_img_path.parts[-1]).as_posix())


if __name__ == '__main__':
    base_path = Path("./_out/")

    with ThreadPoolExecutor() as executor:
        executor.map(combine_and_write, filter(lambda x: x.is_dir(), base_path.glob("*")))
