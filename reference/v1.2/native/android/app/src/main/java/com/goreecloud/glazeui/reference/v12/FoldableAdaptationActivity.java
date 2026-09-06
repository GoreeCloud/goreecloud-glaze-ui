package com.goreecloud.glazeui.reference.v12;

import android.app.Activity;
import android.content.res.Configuration;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Locale;

/**
 * Bounded Android window-size adaptation reference for GLAZE UI V1.2.
 *
 * This reference responds only to the window configuration Android exposes to
 * the activity. Optional hinge width is producer-supplied test/application data;
 * this activity does not inspect hinge sensors, posture APIs, or OEM features.
 */
public final class FoldableAdaptationActivity extends Activity {
    static final int WIDE_THRESHOLD_DP = 780;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(buildContent());
    }

    private View buildContent() {
        Configuration configuration = getResources().getConfiguration();
        int widthDp = configuration.screenWidthDp;
        boolean wide = widthDp >= WIDE_THRESHOLD_DP;
        int hingeWidthDp = Math.max(0, Math.min(96, getIntent().getIntExtra("hingeWidthDp", 0)));

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(24), dp(28), dp(24), dp(28));
        page.setBackgroundColor(Color.rgb(239, 242, 246));

        TextView eyebrow = text("GLAZE UI V1.2 · ANDROID WINDOW ADAPTATION", 12, Color.rgb(47, 111, 237));
        page.addView(eyebrow);

        String mode = wide ? "wide" : "compact";
        int panels = wide ? 2 : 1;
        String summary = String.format(
            Locale.ROOT,
            "Foldable adaptation: %s\nWindow width dp: %d\nPanels: %d",
            mode,
            widthDp,
            panels
        );
        if (wide && hingeWidthDp > 0) {
            summary += "\nHinge exclusion: " + hingeWidthDp + " dp (producer-provided)";
        } else {
            summary += "\nHinge exclusion: none";
        }

        TextView status = text(summary, 18, Color.rgb(25, 25, 28));
        status.setContentDescription(summary.replace('\n', ';'));
        status.setPadding(0, dp(14), 0, dp(20));
        page.addView(status);

        if (wide) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.TOP);
            row.addView(panel("Primary task", "List / current work remains present."), weighted());
            if (hingeWidthDp > 0) {
                View hinge = new View(this);
                hinge.setContentDescription("Producer-provided hinge exclusion " + hingeWidthDp + " dp");
                row.addView(hinge, new LinearLayout.LayoutParams(dp(hingeWidthDp), dp(220)));
            }
            row.addView(panel("Added context", "Wide space adds detail rather than only scaling."), weighted());
            page.addView(row, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ));
        } else {
            page.addView(panel("Primary task", "Single-panel complete environment."));
        }

        TextView boundary = text(
            "Boundary: Android emulator/window-size adaptation only. No hinge sensor, OEM posture semantics, "
                + "physical foldable qualification, production, RC, or Stable authority.",
            13,
            Color.rgb(92, 92, 99)
        );
        boundary.setPadding(0, dp(24), 0, 0);
        page.addView(boundary);
        return page;
    }

    private LinearLayout.LayoutParams weighted() {
        return new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
    }

    private TextView panel(String heading, String body) {
        TextView panel = text(heading + "\n" + body, 16, Color.rgb(25, 25, 28));
        panel.setPadding(dp(18), dp(18), dp(18), dp(18));
        panel.setMinHeight(dp(180));
        panel.setBackgroundColor(Color.rgb(252, 253, 255));
        return panel;
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
