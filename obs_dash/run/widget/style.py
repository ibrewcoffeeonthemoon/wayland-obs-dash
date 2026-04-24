CSS = '''
    window {
        background-color: transparent;
    }
    box {
        border-radius: 12px;
        padding: 10px;
        transition: background-color 0.5s ease; /* Smooth color transition */
        background-color: #828282;
    }
    picture {
        border-radius: 6px;
    }
    .preview-box {
        background-color: transparent;
        border: none;
        box-shadow: none;
        padding: 0px;
        margin: 0px;
    }
    .disconnected {
        background-color: #828282;
    }
    .connected {
        background-color: #0d6b02;
    }
    .recording {
        background-color: #a1000b;
    }
    label {
        color: white;
        font-weight: bold;
        font-size: 24px;
        margin: auto;
    }
    levelbar block {
        opacity: 0.8;
        border: none;
        width: 4px;
        min-width: 4px;
    }
    levelbar block.empty {
        background-color: transparent;
        border-color: transparent;
    }
    levelbar block.low {
        background-color: #2ec27e; /* OBS Green */
    }
    levelbar block.high {
        background-color: #f5c211; /* OBS Yellow */
    }
    levelbar block.full {
        background-color: #e01b24; /* OBS Red */
    }
'''
