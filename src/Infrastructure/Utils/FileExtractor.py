import os
import pypdf
import docx
import io

class FileExtractor:
    @staticmethod
    def extract_text_from_file(uploaded_file) -> str:
        """
        Extracts text from an InMemoryUploadedFile (PDF or DOCX).
        Returns the extracted text string.
        Raises ValueError if format is unsupported or file is corrupt.
        """
        filename = uploaded_file.name.lower()
        file_bytes = uploaded_file.read()
        file_stream = io.BytesIO(file_bytes)

        try:
            if filename.endswith('.pdf'):
                return FileExtractor._extract_from_pdf(file_stream)
            elif filename.endswith('.docx'):
                return FileExtractor._extract_from_docx(file_stream)
            else:
                raise ValueError(f"Formato no soportado: {filename}. Usa PDF o DOCX.")
        except Exception as e:
            raise ValueError(f"Error procesando archivo: {str(e)}")

    @staticmethod
    def _extract_from_pdf(stream) -> str:
        reader = pypdf.PdfReader(stream)
        text = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)
        return "\n".join(text)

    @staticmethod
    def _extract_from_docx(stream) -> str:
        doc = docx.Document(stream)
        text = [para.text for para in doc.paragraphs]
        return "\n".join(text)
