SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string", "const": "1.0"},
        "target": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["selected", "collection", "smartCollection", "folder", "all"]},
                "identifier": {"type": "string"},
                "createVirtualCopy": {"type": "boolean"}
            },
            "required": ["scope", "createVirtualCopy"]
        },
        "pipeline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "stage": {"type": "string", "enum": ["base", "toneCurve", "HSL", "detail", "effects", "calibration", "local", "preset"]},
                    "settings": {"type": "object"},
                    "rgb": {"type": "array"},
                    "hue": {"type": "object"},
                    "sat": {"type": "object"},
                    "lum": {"type": "object"},
                    "sharpen": {"type": "object"},
                    "nr": {"type": "object"},
                    "grain": {"type": "object"},
                    "vignette": {"type": "object"},
                    "redPrimary": {"type": "object"},
                    "greenPrimary": {"type": "object"},
                    "bluePrimary": {"type": "object"},
                    "brushes": {"type": "array"},
                    "apply": {"type": "array"},
                    "blend": {"type": "object"}
                },
                "required": ["stage"]
            }
        },
        "export": {
            "type": "object",
            "properties": {
                "enable": {"type": "boolean"},
                "preset": {"type": "string"},
                "dest": {"type": "string"}
            },
            "required": ["enable"]
        },
        "safety": {
            "type": "object",
            "properties": {
                "snapshot": {"type": "boolean"},
                "dryRun": {"type": "boolean"}
            },
            "required": ["snapshot", "dryRun"]
        }
    },
    "required": ["version", "pipeline", "safety"]
}
