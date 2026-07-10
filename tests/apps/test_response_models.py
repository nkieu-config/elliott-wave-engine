"""Round-trip the dumped payload fixtures through the response models, so a
field that dumps to something the model would reject fails without a full
endpoint pipeline run.
"""

from __future__ import annotations

import pytest

from apps.api.schemas_responses import Layer1Response, PipelineResponse


@pytest.mark.slow
def test_pipeline_payload_matches_response_model(payload):
    PipelineResponse.model_validate(payload)


@pytest.mark.slow
def test_layer1_payload_matches_response_model(layer1_payload):
    Layer1Response.model_validate(layer1_payload)
