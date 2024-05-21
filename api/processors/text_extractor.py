from paddleocr import PaddleOCR
import re


class TextExtractor:
    def __init__(self, image):
        self.image = image
        self.ocr = PaddleOCR(use_angle_cls=True, lang="id", use_gpu=False)
        self.extracted_text = self.extract_text(image)

    def extract_text(self, image):
        """
        Extracts text from an image using OCR (Optical Character Recognition).

        Args:
            image: The image from which to extract text.

        Returns:
            The extracted text as a string.

        Raises:
            None.
        """
        result = self.ocr.ocr(image, cls=True)
        if not result or not result[0]:
            print("OCR did not return any results.")
            return ""

        clean_result = [line for line in result[0]]
        grouped_text = self._group_inline(clean_result)
        cleaned_lines = [self._preprocess_text(line) for line in grouped_text]
        cleaned_lines = [line.strip() for line in cleaned_lines if line.strip()]
        extracted_text = "\n".join(cleaned_lines).lower()

        return extracted_text

    def _preprocess_text(self, line):
        """
        Preprocesses a line of text by performing various transformations.

        Args:
            line (str): The input line of text to be preprocessed.

        Returns:
            str: The preprocessed line of text.

        """
        dates = re.findall(r"\b\d{2}[./-]\d{2}[./-]\d{2,4}\b", line)
        line = re.sub(r"\brp[.\s]?", "", line, flags=re.IGNORECASE)
        line = re.sub(r"[^\w\s.,]", "", line)
        for date in dates:
            line += f" {date}"
        line = re.sub(r"\b[a-zA-Z]\b", " ", line)
        line = re.sub(r"(?<!\d)[.,](?!\d)|(?<!\b[a-zA-Z])[.,](?!\b[a-zA-Z])", "", line)
        line = re.sub(r"\b\d\b", "", line)
        line = re.sub(r"^\s*$\n", "", line, flags=re.MULTILINE)
        line = re.sub(r"\s+", " ", line).strip()
        return line

    def _group_inline(self, ocr_result, tolerance=15):
        """
        Groups consecutive lines of text that are considered to be inline based on their position.

        Args:
            ocr_result (list): A list of tuples representing the OCR result, where each tuple contains the position and text of a line.
            tolerance (int, optional): The maximum vertical distance allowed between two lines to be considered inline. Defaults to 15.

        Returns:
            list: A list of grouped text strings, where each string represents a group of inline lines.

        """
        grouped_result = []
        temp = ocr_result[0]
        for i in range(1, len(ocr_result)):
            if not self._is_inline(ocr_result[i - 1][0], ocr_result[i][0], tolerance):
                joined_text = " ".join(
                    [
                        line[1][0]
                        for line in ocr_result[
                            ocr_result.index(temp) : ocr_result.index(ocr_result[i])
                        ]
                    ]
                )
                grouped_result.append(joined_text.lower())
                temp = ocr_result[i]
        return grouped_result

    def _is_inline(self, box1, box2, tolerance):
        """
        Check if two bounding boxes are inline with each other within a given tolerance.

        Parameters:
        - box1: The first bounding box, represented as a list of four points [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].
        - box2: The second bounding box, represented as a list of four points [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].
        - tolerance: The maximum allowed difference in y-coordinates for the boxes to be considered inline.

        Returns:
        - True if the boxes are inline, False otherwise.
        """
        top_aligned = abs(box1[0][1] - box2[0][1]) <= tolerance
        bottom_aligned = abs(box1[2][1] - box2[2][1]) <= tolerance
        return top_aligned and bottom_aligned
