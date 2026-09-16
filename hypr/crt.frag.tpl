// Cogitator global CRT treatment for Hyprland screen_shader.
// Rendered from this template by scripts/cogitator (prepare_config):
// {{SCAN}}, {{VIGNETTE}} are 0..1-scale floats.
//
// Deliberately STATIC (no `time` uniform): Hyprland only runs time-based
// screen shaders with damage tracking disabled, which forces full-frame
// GPU renders constantly. Scanlines + vignette cache with damaged frames
// at zero continuous cost; flicker and grain live in the small-region
// QML overlays instead. Darkens only — never recolors, so applications
// keep their fidelity.
#version 300 es
precision mediump float;
in vec2 v_texcoord;
uniform sampler2D tex;
out vec4 fragColor;

void main() {
    vec4 c = texture(tex, v_texcoord);

    // Horizontal scanlines, ~540 across the screen height.
    float scan = 1.0 - ({{SCAN}} * step(0.5, fract(v_texcoord.y * 540.0)));

    // Soft edge falloff.
    vec2 d = v_texcoord - vec2(0.5);
    float vig = 1.0 - ({{VIGNETTE}} * dot(d, d) * 2.0);

    fragColor = vec4(c.rgb * scan * vig, c.a);
}
