"""SkyBrain SDK adapter layer.

Only `service.adapters.skybrain_sdk` may import the proprietary `skybrain_sdk`
package. Every endpoint goes through the `SkyBrainAdapter` Protocol defined in
`service.adapters.protocol`. This boundary is enforced by an import-linter
contract configured in `pyproject.toml`.
"""
