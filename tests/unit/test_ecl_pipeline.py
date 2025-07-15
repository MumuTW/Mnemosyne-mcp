"""
ECL Pipeline 整合測試
"""

import tempfile
from unittest.mock import MagicMock

import pytest

from mnemosyne.ecl.pipeline import ECLPipeline


class TestECLPipeline:
    """ECL 管線測試"""

    def test_pipeline_initialization(self):
        """測試管線初始化"""
        mock_driver = MagicMock()
        pipeline = ECLPipeline(mock_driver)

        assert pipeline.driver == mock_driver
        assert pipeline.extractor is None
        assert pipeline.cognifier is not None
        assert pipeline.loader is not None

    @pytest.mark.asyncio
    async def test_process_empty_project(self):
        """測試處理空專案"""
        mock_driver = MagicMock()
        pipeline = ECLPipeline(mock_driver)

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = await pipeline.process_project(tmp_dir)

            assert result.files_extracted == 0
            assert result.functions_found == 0
            assert result.calls_found == 0
            assert result.functions_loaded == 0
            assert result.calls_loaded == 0
            assert len(result.errors) == 1
            assert "沒有找到任何 Python 檔案" in result.errors[0]
            assert result.success is False
