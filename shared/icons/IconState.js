.pragma library

function volumeBands(value) {
    var volume = Number(value);
    return volume >= 0.67 ? 3 : (volume >= 0.34 ? 2 : (volume > 0 ? 1 : 0));
}

function signalBands(value) {
    var strength = Number(value);
    return isFinite(strength) ? Math.max(0, Math.min(4, Math.ceil(strength / 20) - 1)) : 0;
}

function cellCharge(value) {
    var fraction = Number(value);
    return isFinite(fraction) ? Math.max(0, Math.min(1, fraction)) : 0;
}

// Consume the stock resolver's glyph, retaining its source and night decisions.
function weatherKind(glyph) {
    var types = {
        "": "sun", "": "moon", "": "partly-night", "": "partly",
        "": "cloud", "\ue346": "fog", "\ue313": "fog",
        "": "rain", "": "rain", "": "rain",
        "": "snow", "": "snow", "": "snow",
        "": "sleet", "": "storm"
    };
    return types[String(glyph)] || "unknown";
}
