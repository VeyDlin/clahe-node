from PIL import Image
import cv2
import numpy as np


from invokeai.app.services.image_records.image_records_common import ImageCategory, ResourceOrigin
from invokeai.app.invocations.baseinvocation import (
    BaseInvocation,
    InputField,
    invocation,
    InvocationContext,
    WithMetadata,
    WithWorkflow,
)

from invokeai.app.invocations.primitives import (
    ImageField,
    ImageOutput
)


@invocation(
    "contrast_limiteda_daptive_histogram_equalization",
    title="Contrast Limited Adaptive Histogram Equalization",
    tags=["image", "adaptive", "CLAHE"],
    category="image",
    version="1.0.0",
)
class CLAHEInvocation(BaseInvocation, WithMetadata, WithWorkflow):
    """Contrast Limited Adaptive Histogram Equalization"""
    image: ImageField = InputField(default=None, description="Input image")

    clip_limit: float = InputField(default=0.5, description="Threshold used to limit the contrast during the AHE process")
    tile_grid_size: int = InputField(default=8, description="Size of the region or \"tile\" (in pixels) over which the equalization is applied")


    def invoke(self, context: InvocationContext) -> ImageOutput:
        image = context.services.images.get_pil_image(self.image.image_name)  
        numpy_image = np.array(image)
        cv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)

        lab_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2Lab)
        l, a, b = cv2.split(lab_image)

        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=(self.tile_grid_size, self.tile_grid_size))
        l_clahe = clahe.apply(l)

        lab_image_clahe = cv2.merge((l_clahe, a, b))

        cv_image = cv2.cvtColor(lab_image_clahe, cv2.COLOR_Lab2BGR)

        image_dto = context.services.images.create(
            image=Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGRA2RGBA)),
            image_origin=ResourceOrigin.INTERNAL,
            image_category=ImageCategory.GENERAL,
            node_id=self.id,
            session_id=context.graph_execution_state_id,
            is_intermediate=self.is_intermediate,
            workflow=self.workflow,
        )

        return ImageOutput(
            image=ImageField(image_name=image_dto.image_name),
            width=image_dto.width,
            height=image_dto.height,
        )