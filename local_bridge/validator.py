import jsonschema
from schema import SCHEMA

def validate_config(config_instance):
    """
    Validates a given configuration instance against the LrDevConfig v1 schema.

    Args:
        config_instance (dict): The configuration dictionary to validate.

    Returns:
        tuple[bool, str | None]: A tuple containing a boolean indicating validity,
                                 and an error message string if invalid.
    """
    try:
        jsonschema.validate(instance=config_instance, schema=SCHEMA)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        # Provide a more concise error message
        error_message = f"Schema validation failed at '{'.'.join(map(str, e.path))}': {e.message}"
        return False, error_message
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    # Test with a valid config
    valid_config = {
        "version": "1.0",
        "target": {
            "scope": "selected",
            "createVirtualCopy": True
        },
        "pipeline": [
            {
                "stage": "base",
                "settings": {
                    "Exposure": -0.15
                }
            }
        ],
        "export": {
            "enable": False
        },
        "safety": {
            "snapshot": True,
            "dryRun": True
        }
    }

    is_valid, msg = validate_config(valid_config)
    print(f"Testing valid config... Valid: {is_valid}, Message: {msg}")
    assert is_valid

    # Test with an invalid config (missing 'safety' required property)
    invalid_config = {
        "version": "1.0",
        "pipeline": [
            {
                "stage": "base"
            }
        ]
    }

    is_valid, msg = validate_config(invalid_config)
    print(f"Testing invalid config... Valid: {is_valid}, Message: {msg}")
    assert not is_valid

    # Test with another invalid config (wrong stage enum)
    invalid_config_2 = {
        "version": "1.0",
        "pipeline": [
            {
                "stage": "invalid_stage_name"
            }
        ],
        "safety": {
            "snapshot": True,
            "dryRun": True
        }
    }

    is_valid, msg = validate_config(invalid_config_2)
    print(f"Testing another invalid config... Valid: {is_valid}, Message: {msg}")
    assert not is_valid

    print("\nValidator tests passed!")
