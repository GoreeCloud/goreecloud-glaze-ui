package com.goreecloud.glazeui.reference.v12;

import android.app.WallpaperColors;
import android.app.WallpaperManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;

/**
 * Consumer/platform adapter reference for GLAZE UI V1.2 Personalization.
 *
 * Authority boundary: this class belongs to the bounded Android reference
 * consumer. It may translate Android-owned system summaries and persist the
 * reference consumer's own preference envelope. It never reads raw wallpaper
 * pixels, transmits wallpaper content, performs network I/O, or grants Glaze
 * core persistence/wallpaper ownership.
 */
final class AndroidPersonalizationPlatformAdapter {
    static final int STORAGE_SCHEMA_VERSION = 1;
    static final String STORAGE_NAME = "goreecloud_glaze_v12_candidate_consumer_reference";
    private static final String KEY_SCHEMA = "schema";
    private static final String KEY_APPEARANCE = "appearance";
    private static final String KEY_CLARITY = "clarity";

    private final Context appContext;

    AndroidPersonalizationPlatformAdapter(Context context) {
        appContext = context.getApplicationContext();
    }

    WallpaperSummary readSystemWallpaperSummary() {
        WallpaperColors colors = WallpaperManager.getInstance(appContext)
            .getWallpaperColors(WallpaperManager.FLAG_SYSTEM);
        if (colors == null || colors.getPrimaryColor() == null) return null;
        int argb = colors.getPrimaryColor().toArgb();
        return new WallpaperSummary(Color.red(argb), Color.green(argb), Color.blue(argb));
    }

    void saveCandidatePreferences(String appearance, String clarity) {
        if (!validAppearance(appearance) || !validClarity(clarity)) {
            clearCandidatePreferences();
            return;
        }
        preferences().edit()
            .putInt(KEY_SCHEMA, STORAGE_SCHEMA_VERSION)
            .putString(KEY_APPEARANCE, appearance)
            .putString(KEY_CLARITY, clarity)
            .apply();
    }

    StoredPreferences loadCandidatePreferences() {
        SharedPreferences preferences = preferences();
        if (preferences.getInt(KEY_SCHEMA, -1) != STORAGE_SCHEMA_VERSION) return null;
        String appearance = preferences.getString(KEY_APPEARANCE, null);
        String clarity = preferences.getString(KEY_CLARITY, null);
        if (!validAppearance(appearance) || !validClarity(clarity)) return null;
        return new StoredPreferences(appearance, clarity, STORAGE_SCHEMA_VERSION);
    }

    void clearCandidatePreferences() {
        preferences().edit().clear().apply();
    }

    private SharedPreferences preferences() {
        return appContext.getSharedPreferences(STORAGE_NAME, Context.MODE_PRIVATE);
    }

    private static boolean validAppearance(String value) {
        return "follow-system".equals(value)
            || "light".equals(value)
            || "dark".equals(value)
            || "deep-dark".equals(value);
    }

    private static boolean validClarity(String value) {
        return "clear".equals(value) || "balanced".equals(value) || "dense".equals(value);
    }

    static final class WallpaperSummary {
        final int r;
        final int g;
        final int b;

        WallpaperSummary(int r, int g, int b) {
            this.r = r;
            this.g = g;
            this.b = b;
        }
    }

    static final class StoredPreferences {
        final String appearance;
        final String clarity;
        final int schemaVersion;

        StoredPreferences(String appearance, String clarity, int schemaVersion) {
            this.appearance = appearance;
            this.clarity = clarity;
            this.schemaVersion = schemaVersion;
        }
    }
}
