package com.goreecloud.glazeui.reference.v12;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Locale;

/**
 * Runtime harness for the Android consumer/platform Personalization adapter.
 * This is Candidate evidence only and is deliberately separate from Glaze core.
 */
public final class PlatformAdapterActivity extends Activity {
    private AndroidPersonalizationPlatformAdapter adapter;
    private TextView status;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        adapter = new AndroidPersonalizationPlatformAdapter(this);
        setContentView(buildContent());

        String mode = getIntent().getStringExtra("mode");
        if ("wallpaper".equals(mode)) {
            runWallpaperSummaryCase();
        } else if ("persist".equals(mode)) {
            persistCase();
        } else if ("load".equals(mode)) {
            loadCase();
        } else if ("clear".equals(mode)) {
            adapter.clearCandidatePreferences();
            updateStatus("Storage cleared");
        } else {
            updateStatus("Adapter mode: invalid (fail-closed)");
        }
    }

    private void runWallpaperSummaryCase() {
        updateStatus("WallpaperColors adapter: Pending");
        Thread worker = new Thread(() -> {
            AndroidPersonalizationPlatformAdapter.WallpaperSummary summary =
                adapter.readSystemWallpaperSummary();
            runOnUiThread(() -> {
                if (summary == null) {
                    updateStatus("WallpaperColors adapter: Unavailable (fail-closed)");
                } else {
                    updateStatus(String.format(
                        Locale.ROOT,
                        "WallpaperColors adapter: Available\nSystem RGB summary: %d,%d,%d",
                        summary.r,
                        summary.g,
                        summary.b
                    ));
                }
            });
        }, "glaze-v12-wallpaper-colors-summary");
        worker.start();
    }

    private void persistCase() {
        String appearance = normalizeAppearance(getIntent().getStringExtra("appearance"));
        String clarity = normalizeClarity(getIntent().getStringExtra("clarity"));
        adapter.saveCandidatePreferences(appearance, clarity);
        showStored(adapter.loadCandidatePreferences());
    }

    private void loadCase() {
        showStored(adapter.loadCandidatePreferences());
    }

    private void showStored(AndroidPersonalizationPlatformAdapter.StoredPreferences stored) {
        if (stored == null) {
            updateStatus("Stored preferences: None");
            return;
        }
        updateStatus(
            "Stored appearance: " + label(stored.appearance)
                + "\nStored clarity: " + label(stored.clarity)
                + "\nStorage schema: " + stored.schemaVersion
        );
    }

    private String normalizeAppearance(String value) {
        if (value == null) return "follow-system";
        String candidate = value.toLowerCase(Locale.ROOT);
        if ("light".equals(candidate) || "dark".equals(candidate) || "deep-dark".equals(candidate)) {
            return candidate;
        }
        return "follow-system";
    }

    private String normalizeClarity(String value) {
        if (value == null) return "balanced";
        String candidate = value.toLowerCase(Locale.ROOT);
        if ("clear".equals(candidate) || "dense".equals(candidate)) return candidate;
        return "balanced";
    }

    private String label(String value) {
        if ("follow-system".equals(value)) return "Follow System";
        if ("deep-dark".equals(value)) return "Deep Dark";
        return value.substring(0, 1).toUpperCase(Locale.ROOT) + value.substring(1);
    }

    private LinearLayout buildContent() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(24), dp(36), dp(24), dp(36));
        page.setGravity(Gravity.TOP);
        page.setBackgroundColor(Color.rgb(239, 242, 246));

        TextView title = text("GLAZE UI V1.2 · ANDROID PLATFORM ADAPTER", 12, Color.rgb(47, 111, 237));
        page.addView(title);
        TextView heading = text("Consumer-owned native integration evidence", 24, Color.rgb(25, 25, 28));
        heading.setPadding(0, dp(12), 0, dp(18));
        page.addView(heading);

        status = text("Adapter: Ready", 17, Color.rgb(25, 25, 28));
        status.setMinHeight(dp(96));
        status.setContentDescription("Android Personalization platform adapter status: Ready");
        page.addView(status);

        TextView boundary = text(
            "Boundary: system WallpaperColors summary and reference-consumer preference storage only. "
                + "No raw wallpaper pixels, wallpaper transmission, Glaze-core persistence ownership, "
                + "cross-device sync, physical-device qualification, production, RC, or Stable authority.",
            13,
            Color.rgb(92, 92, 99)
        );
        boundary.setPadding(0, dp(24), 0, 0);
        page.addView(boundary);
        return page;
    }

    private void updateStatus(String value) {
        status.setText(value);
        status.setContentDescription(value.replace('\n', ';'));
    }

    private TextView text(String value, int sp, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setLineSpacing(0f, 1.18f);
        return view;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
