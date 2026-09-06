package com.goreecloud.glazeui.reference.v12;

import android.app.Activity;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.Locale;

/**
 * Bounded Android framework-native adapter reference for GLAZE UI V1.2
 * Personalization + Living Frosted. Authority boundary: no persistence, synchronization, wallpaper acquisition, telemetry, network
 * transport, or lifecycle promotion authority.
 */
public final class PersonalizationActivity extends Activity {
    public static final int MIN_TOUCH_DP = 48;
    public static final int TOUCH_ASSISTANCE_DP = 56;
    public static final float WALLPAPER_ALPHA = 0.08f;
    public static final float WALLPAPER_MAX_ALPHA = 0.12f;
    public static final float WALLPAPER_CHROMA_RETENTION = 0.24f;
    public static final float WALLPAPER_MAX_CHROMA_RETENTION = 0.28f;

    private String appearancePreference;
    private String resolvedAppearance;
    private String clarity;
    private boolean reducedTransparency;
    private boolean touchAssistance;
    private int targetFloorDp;
    private WallpaperAtmosphere wallpaperAtmosphere;

    private int canvas;
    private int raised;
    private int text;
    private int secondary;
    private int line;
    private int accent;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        appearancePreference = normalizeAppearancePreference(getIntent().getStringExtra("appearance"));
        resolvedAppearance = resolveAppearance(appearancePreference, getResources().getConfiguration());
        clarity = normalizeClarity(getIntent().getStringExtra("clarity"));
        reducedTransparency = getIntent().getBooleanExtra("reducedTransparency", false);
        touchAssistance = getIntent().getBooleanExtra("touchAssistance", false);
        targetFloorDp = touchAssistance ? TOUCH_ASSISTANCE_DP : MIN_TOUCH_DP;
        wallpaperAtmosphere = reducedTransparency ? null : readWallpaperAtmosphere();

        resolvePalette();
        configureWindow();
        setContentView(buildContent());
    }

    static String normalizeAppearancePreference(String requested) {
        if (requested == null) return "follow-system";
        String value = requested.toLowerCase(Locale.ROOT);
        if ("light".equals(value) || "dark".equals(value) || "deep-dark".equals(value)) return value;
        return "follow-system";
    }

    static String resolveAppearance(String preference, Configuration configuration) {
        if ("light".equals(preference) || "dark".equals(preference) || "deep-dark".equals(preference)) {
            return preference;
        }
        int night = configuration.uiMode & Configuration.UI_MODE_NIGHT_MASK;
        return night == Configuration.UI_MODE_NIGHT_YES ? "dark" : "light";
    }

    static String normalizeClarity(String requested) {
        if (requested == null) return "balanced";
        String value = requested.toLowerCase(Locale.ROOT);
        if ("clear".equals(value) || "dense".equals(value)) return value;
        return "balanced";
    }

    private WallpaperAtmosphere readWallpaperAtmosphere() {
        if (!getIntent().hasExtra("wallpaperR") || !getIntent().hasExtra("wallpaperG") || !getIntent().hasExtra("wallpaperB")) {
            return null;
        }
        return deriveWallpaperAtmosphere(
            getIntent().getIntExtra("wallpaperR", -1),
            getIntent().getIntExtra("wallpaperG", -1),
            getIntent().getIntExtra("wallpaperB", -1)
        );
    }

    static WallpaperAtmosphere deriveWallpaperAtmosphere(int r, int g, int b) {
        if (!validChannel(r) || !validChannel(g) || !validChannel(b)) return null;
        int luminance = Math.round(r * 0.2126f + g * 0.7152f + b * 0.0722f);
        int outR = desaturate(r, luminance);
        int outG = desaturate(g, luminance);
        int outB = desaturate(b, luminance);
        return new WallpaperAtmosphere(outR, outG, outB, WALLPAPER_ALPHA, WALLPAPER_CHROMA_RETENTION);
    }

    private static boolean validChannel(int value) {
        return value >= 0 && value <= 255;
    }

    private static int desaturate(int channel, int luminance) {
        return clamp(Math.round(luminance + (channel - luminance) * WALLPAPER_CHROMA_RETENTION), 0, 255);
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private void resolvePalette() {
        accent = Color.rgb(82, 151, 181);
        if ("deep-dark".equals(resolvedAppearance)) {
            canvas = Color.rgb(8, 8, 10);
            raised = Color.rgb(31, 31, 34);
            text = Color.rgb(247, 247, 248);
            secondary = Color.rgb(188, 188, 194);
            line = Color.rgb(74, 74, 80);
        } else if ("dark".equals(resolvedAppearance)) {
            canvas = Color.rgb(18, 18, 20);
            raised = Color.rgb(42, 42, 45);
            text = Color.rgb(247, 247, 248);
            secondary = Color.rgb(188, 188, 194);
            line = Color.rgb(76, 76, 82);
        } else {
            canvas = Color.rgb(239, 242, 246);
            raised = Color.rgb(252, 252, 252);
            text = Color.rgb(25, 25, 28);
            secondary = Color.rgb(92, 92, 99);
            line = Color.rgb(205, 208, 214);
        }
    }

    private void configureWindow() {
        Window window = getWindow();
        window.setStatusBarColor(canvas);
        window.setNavigationBarColor(canvas);
        int flags = window.getDecorView().getSystemUiVisibility();
        int lightFlags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        if ("light".equals(resolvedAppearance)) flags |= lightFlags;
        else flags &= ~lightFlags;
        window.getDecorView().setSystemUiVisibility(flags);
    }

    private View buildContent() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(canvas);
        scroll.setContentDescription("GLAZE UI V1.2 Android Personalization adapter scroll container");

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(20), dp(28), dp(20), dp(36));
        page.setBackgroundColor(canvas);

        add(page, heading("GLAZE UI V1.2 · PERSONALIZATION CANDIDATE", 12), 8);
        add(page, heading("Native adapter evidence", 28), 10);
        add(page, body("System appearance, Living Frosted Clarity, and bounded local wallpaper-atmosphere derivation are exercised without persistence, synchronization, wallpaper acquisition, telemetry, or remote content."), 18);

        LinearLayout evidence = panel();
        add(evidence, fact("Appearance preference", appearancePreferenceLabel()), 6);
        add(evidence, fact("Resolved appearance", appearanceLabel(resolvedAppearance)), 6);
        add(evidence, fact("Clarity", clarityLabel()), 6);
        add(evidence, fact("Reduced Transparency", reducedTransparency ? "Enabled" : "Disabled"), 6);
        add(evidence, fact("Target floor", targetFloorDp + " dp"), 6);
        if (wallpaperAtmosphere == null) {
            add(evidence, fact("Wallpaper atmosphere", "None"), 0);
        } else {
            add(evidence, fact("Wallpaper atmosphere", "Local bounded RGB summary"), 6);
            add(evidence, fact("Wallpaper alpha", formatFloat(wallpaperAtmosphere.alpha)), 6);
            add(evidence, fact("Wallpaper chroma retention", formatFloat(wallpaperAtmosphere.chromaRetention)), 0);
        }
        page.addView(evidence, block(16));

        LinearLayout material = panel();
        material.setContentDescription("Living Frosted native material sample; clarity " + clarityLabel());
        if (wallpaperAtmosphere != null) {
            material.setBackground(atmosphericMaterial(wallpaperAtmosphere));
        }
        add(material, heading("Living Frosted", 21), 6);
        add(material, body(reducedTransparency
            ? "Reduced Transparency suppresses decorative wallpaper atmosphere while preserving structure, text, and semantic meaning."
            : "Clarity changes optical expression only. Accessibility and semantic meaning remain authoritative."), 0);
        page.addView(material, block(16));

        Button action = new Button(this);
        action.setAllCaps(false);
        action.setText("Personalization action");
        action.setTextSize(16);
        action.setTextColor(Color.WHITE);
        action.setMinHeight(dp(targetFloorDp));
        action.setMinimumHeight(dp(targetFloorDp));
        action.setPadding(dp(16), 0, dp(16), 0);
        action.setBackground(rounded(accent, 999, accent));
        action.setContentDescription("Personalization action");
        page.addView(action, block(16));

        TextView boundary = body(
            "Evidence boundary: Android emulator adapter behavior is not physical-device qualification, OEM visual acceptance, TalkBack certification, consumer persistence acceptance, wallpaper-source acquisition acceptance, cross-device synchronization, production acceptance, or Stable promotion."
        );
        boundary.setContentDescription("Candidate adapter evidence boundary; not physical device or Stable acceptance");
        page.addView(boundary, block(0));

        scroll.addView(page, new ScrollView.LayoutParams(
            ScrollView.LayoutParams.MATCH_PARENT,
            ScrollView.LayoutParams.WRAP_CONTENT
        ));
        return scroll;
    }

    private LinearLayout panel() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(18), dp(18), dp(18), dp(18));
        layout.setBackground(rounded(raised, 26, line));
        return layout;
    }

    private LayerDrawable atmosphericMaterial(WallpaperAtmosphere atmosphere) {
        GradientDrawable neutralBase = rounded(raised, 26, line);
        GradientDrawable atmosphereOverlay = rounded(Color.argb(
            Math.round(Math.min(atmosphere.alpha, WALLPAPER_MAX_ALPHA) * 255f),
            atmosphere.r,
            atmosphere.g,
            atmosphere.b
        ), 26, Color.TRANSPARENT);
        return new LayerDrawable(new android.graphics.drawable.Drawable[]{neutralBase, atmosphereOverlay});
    }

    private TextView fact(String name, String value) {
        TextView view = body(name + ": " + value);
        view.setContentDescription(name + ": " + value);
        return view;
    }

    private TextView heading(String value, int sp) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextColor(text);
        view.setTextSize(sp);
        return view;
    }

    private TextView body(String value) {
        return body(value, 14);
    }

    private TextView body(String value, int bottomDp) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextColor(secondary);
        view.setTextSize(14);
        view.setLineSpacing(0f, 1.18f);
        view.setPadding(0, 0, 0, dp(bottomDp));
        return view;
    }

    private void add(LinearLayout parent, TextView child, int bottomDp) {
        child.setPadding(child.getPaddingLeft(), child.getPaddingTop(), child.getPaddingRight(), dp(bottomDp));
        parent.addView(child, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ));
    }

    private LinearLayout.LayoutParams block(int bottomDp) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, 0, 0, dp(bottomDp));
        return params;
    }

    private GradientDrawable rounded(int color, int radiusDp, int strokeColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radiusDp));
        drawable.setStroke(dp(1), strokeColor);
        return drawable;
    }

    private String appearancePreferenceLabel() {
        if ("follow-system".equals(appearancePreference)) return "Follow System";
        return appearanceLabel(appearancePreference);
    }

    private String appearanceLabel(String value) {
        if ("deep-dark".equals(value)) return "Deep Dark";
        if ("dark".equals(value)) return "Dark";
        return "Light";
    }

    private String clarityLabel() {
        if ("clear".equals(clarity)) return "Clear";
        if ("dense".equals(clarity)) return "Dense";
        return "Balanced";
    }

    private static String formatFloat(float value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    static final class WallpaperAtmosphere {
        final int r;
        final int g;
        final int b;
        final float alpha;
        final float chromaRetention;

        WallpaperAtmosphere(int r, int g, int b, float alpha, float chromaRetention) {
            this.r = r;
            this.g = g;
            this.b = b;
            this.alpha = alpha;
            this.chromaRetention = chromaRetention;
        }
    }
}
