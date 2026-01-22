"""
Unit tests for AsyncCD48 class.

These tests mock the aioserial communication to test the async CD48 interface
without requiring actual hardware.
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from pycd48 import CD48Error


class TestAsyncCD48:
    """Test cases for AsyncCD48 class."""

    @pytest.fixture
    def mock_aioserial(self) -> MagicMock:
        """Create a mock aioserial instance."""
        mock = MagicMock()
        mock.is_open = True
        mock.port = "/dev/ttyUSB0"
        mock.in_waiting = 100
        mock.write_async = AsyncMock()
        mock.read_async = AsyncMock(return_value=b"OK\r\n")
        mock.reset_input_buffer = Mock()
        mock.close = Mock()
        return mock

    @pytest.fixture
    def mock_aioserial_module(self, mock_aioserial: MagicMock) -> MagicMock:
        """Create a mock aioserial module."""
        mock_module = MagicMock()
        mock_module.AioSerial.return_value = mock_aioserial
        return mock_module

    @pytest.mark.asyncio
    async def test_connect(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test async connection."""
        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48

            cd48 = AsyncCD48(port="/dev/ttyUSB0", init_delay=0)
            await cd48.connect()

            assert cd48.is_connected
            assert cd48.port == "/dev/ttyUSB0"

    @pytest.mark.asyncio
    async def test_context_manager(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test async context manager."""
        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48

            async with AsyncCD48(port="/dev/ttyUSB0", init_delay=0) as cd48:
                assert cd48.is_connected

            mock_aioserial.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_counts_parsed(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test async get_counts with parsing."""
        mock_aioserial.read_async.return_value = b"100 200 300 400 50 25 10 5 0\r\n"

        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48

            async with AsyncCD48(port="/dev/ttyUSB0", init_delay=0) as cd48:
                result = await cd48.get_counts(human_readable=False)

                assert isinstance(result, dict)
                assert len(result["counts"]) == 8
                assert result["counts"][0] == 100
                assert result["overflow"] == 0

    @pytest.mark.asyncio
    async def test_set_channel(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test async set_channel command."""
        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48

            async with AsyncCD48(port="/dev/ttyUSB0", init_delay=0) as cd48:
                await cd48.set_channel(4, A=1, B=1, C=0, D=0)

                mock_aioserial.write_async.assert_called()
                call_args = mock_aioserial.write_async.call_args[0][0]
                assert call_args == b"S41100\r"

    @pytest.mark.asyncio
    async def test_channel_validation(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test channel validation in async mode."""
        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48

            async with AsyncCD48(port="/dev/ttyUSB0", init_delay=0) as cd48:
                with pytest.raises(ValueError, match="Channel must be 0-7"):
                    await cd48.set_channel(8, A=1, B=0, C=0, D=0)

                with pytest.raises(ValueError, match="A must be 0 or 1"):
                    await cd48.set_channel(0, A=2, B=0, C=0, D=0)

    @pytest.mark.asyncio
    async def test_measure_rate(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test async measure_rate."""
        mock_aioserial.read_async.return_value = b"1000 200 300 400 50 25 10 5 0\r\n"

        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48

            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with AsyncCD48(port="/dev/ttyUSB0", init_delay=0) as cd48:
                    result = await cd48.measure_rate(channel=0, duration=1.0)

                    assert result["counts"] == 1000
                    assert result["rate"] == 1000.0
                    assert result["channel"] == 0

    @pytest.mark.asyncio
    async def test_not_connected_error(self) -> None:
        """Test error when not connected."""
        # Create a mock module to avoid import error
        mock_module = MagicMock()
        with patch.dict(sys.modules, {"aioserial": mock_module}):
            from pycd48.async_cd48 import AsyncCD48

            cd48 = AsyncCD48(port="/dev/ttyUSB0")
            # Don't call connect()

            with pytest.raises(CD48Error, match="Not connected"):
                await cd48._send_command("C")

    @pytest.mark.asyncio
    async def test_auto_detect(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test auto-detection in async mode."""
        mock_port = Mock()
        mock_port.device = "/dev/ttyACM0"
        mock_port.vid = 0x04B4  # Cypress VID
        mock_port.description = "CD48"

        with (
            patch.dict(sys.modules, {"aioserial": mock_aioserial_module}),
            patch("serial.tools.list_ports.comports", return_value=[mock_port]),
        ):
            from pycd48.async_cd48 import AsyncCD48

            async with AsyncCD48(init_delay=0) as cd48:
                assert cd48.is_connected


class TestAsyncCD48WithReconnect:
    """Test cases for AsyncCD48WithReconnect class."""

    @pytest.fixture
    def mock_aioserial(self) -> MagicMock:
        """Create a mock aioserial instance."""
        mock = MagicMock()
        mock.is_open = True
        mock.port = "/dev/ttyUSB0"
        mock.in_waiting = 100
        mock.write_async = AsyncMock()
        mock.read_async = AsyncMock(return_value=b"OK\r\n")
        mock.reset_input_buffer = Mock()
        mock.close = Mock()
        return mock

    @pytest.fixture
    def mock_aioserial_module(self, mock_aioserial: MagicMock) -> MagicMock:
        """Create a mock aioserial module."""
        mock_module = MagicMock()
        mock_module.AioSerial.return_value = mock_aioserial
        return mock_module

    @pytest.mark.asyncio
    async def test_reconnect_on_failure(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test automatic reconnection on command failure."""
        call_count = 0

        async def failing_then_success(*args: object) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("Connection lost")
            return b"OK\r\n"

        mock_aioserial.write_async.side_effect = failing_then_success

        reconnect_called = False

        def on_reconnect() -> None:
            nonlocal reconnect_called
            reconnect_called = True

        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48WithReconnect

            with patch("asyncio.sleep", new_callable=AsyncMock):
                cd48 = AsyncCD48WithReconnect(
                    port="/dev/ttyUSB0",
                    init_delay=0,
                    on_reconnect=on_reconnect,
                    reconnect_delay=0.01,
                )
                await cd48.connect()

                # This should trigger reconnection
                await cd48._send_command("C")

                assert reconnect_called

    @pytest.mark.asyncio
    async def test_disconnect_callback(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test disconnect callback is called."""
        mock_aioserial.write_async.side_effect = OSError("Connection lost")

        disconnect_called = False

        def on_disconnect() -> None:
            nonlocal disconnect_called
            disconnect_called = True

        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48WithReconnect

            with patch("asyncio.sleep", new_callable=AsyncMock):
                cd48 = AsyncCD48WithReconnect(
                    port="/dev/ttyUSB0",
                    init_delay=0,
                    on_disconnect=on_disconnect,
                    max_reconnect_attempts=1,
                    reconnect_delay=0.01,
                )
                await cd48.connect()

                with pytest.raises(CD48Error):
                    await cd48._send_command("C")

                assert disconnect_called

    @pytest.mark.asyncio
    async def test_manual_reconnect(
        self, mock_aioserial: MagicMock, mock_aioserial_module: MagicMock
    ) -> None:
        """Test manual reconnect method."""
        with patch.dict(sys.modules, {"aioserial": mock_aioserial_module}):
            from pycd48.async_cd48 import AsyncCD48WithReconnect

            cd48 = AsyncCD48WithReconnect(port="/dev/ttyUSB0", init_delay=0)
            await cd48.connect()

            # Simulate disconnect
            cd48._connected = False

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await cd48.reconnect()
                assert result is True
                assert cd48.is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
