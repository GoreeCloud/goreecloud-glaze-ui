package com.goreecloud.glazeui.reference.v12;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.Locale;
import static com.goreecloud.glazeui.reference.v12.OpticalPalette.*;

/** Bounded V1.2 Frosted Optical Android reference; no OEM backdrop-blur claim. */
public final class OpticalActivity extends Activity {
    public static final int MIN_TOUCH_DP=48, ASSISTED_TOUCH_DP=56;
    private String appearance, profile;
    private boolean reduced;
    private int target, canvas, material, raised, panel, text, secondary, edge, atmosphere;
    private float atmosphereStrength;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        appearance=norm(getIntent().getStringExtra("appearance"),"light","dark","deep-dark");
        profile=norm(getIntent().getStringExtra("performanceProfile"),"full","reduced","minimal");
        reduced=getIntent().getBooleanExtra("reducedTransparency",false);
        target=getIntent().getBooleanExtra("touchAssistance",false)?ASSISTED_TOUCH_DP:MIN_TOUCH_DP;
        resolve();
        setContentView(content());
    }

    private String norm(String value,String fallback,String... allowed) {
        String v=value==null?fallback:value.toLowerCase(Locale.ROOT);
        for(String a:allowed) if(a.equals(v)) return v;
        return fallback;
    }

    private void resolve() {
        if("deep-dark".equals(appearance)) {
            canvas=BLUE_BLACK; material=alpha(DEEP_GRAPHITE,190); raised=alpha(COOL_GRAPHITE,210);
            panel=alpha(COOL_GRAPHITE,232); text=FROST_WHITE; secondary=CLOUD_GRAY;
            edge=alpha(FROST_WHITE,54); atmosphere=GLACIER_BLUE;
        } else if("dark".equals(appearance)) {
            canvas=COOL_GRAPHITE; material=alpha(COOL_GRAPHITE,184); raised=alpha(DEEP_GRAPHITE,208);
            panel=alpha(DEEP_GRAPHITE,232); text=FROST_WHITE; secondary=CLOUD_GRAY;
            edge=alpha(FROST_WHITE,58); atmosphere=GLACIER_BLUE;
        } else {
            canvas=CLOUD_GRAY; material=alpha(FROST_WHITE,164); raised=alpha(CRYSTAL_WHITE,194);
            panel=alpha(FROST_WHITE,230); text=COOL_GRAPHITE; secondary=SLATE_GRAY;
            edge=alpha(CRYSTAL_WHITE,184); atmosphere=ICE_BLUE;
        }
        atmosphereStrength="full".equals(profile)?1f:("reduced".equals(profile)?.45f:0f);
        if("reduced".equals(profile)) { material=alpha(material,220); raised=alpha(raised,232); panel=alpha(panel,244); }
        if("minimal".equals(profile)||reduced) { material=opaque(material); raised=opaque(raised); panel=opaque(panel); atmosphereStrength=0f; }
    }

    private View content() {
        ScrollView scroll=new ScrollView(this);
        LinearLayout page=new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL); page.setPadding(dp(18),dp(24),dp(18),dp(28));
        page.setBackground(atmosphereStrength==0f?shape(canvas,0,canvas):environment());
        page.addView(card("GLAZE UI V1.2 CANDIDATE\nFrost White is the material.\nWhite behaves as light. Ice Blue behaves as atmosphere.",material,26));
        String mode=reduced||"minimal".equals(profile)?"Opaque Frost":"Frost White";
        page.addView(card("Lifecycle · V1.2 Candidate\nAppearance · "+appearanceLabel()+"\nPerformance · "+profileLabel()+
            "\nMaterial · "+mode+"\nPrimary material: Frost White\nPrimary atmosphere: Ice Blue\nLegacy teal/amber atmosphere: retired",material,22));

        TextView search=card("Universal Search · Clear Frost\nSearch GoreeCloud",raised,999);
        search.setMinHeight(dp(target)); search.setContentDescription("Universal Search Clear Frost"); page.addView(search);

        LinearLayout quick=new LinearLayout(this); quick.setOrientation(LinearLayout.VERTICAL);
        quick.setPadding(dp(16),dp(16),dp(16),dp(16)); quick.setBackground(shape(panel,26,mix(edge,GLACIER_BLUE,.30f)));
        quick.addView(label("Quick Settings · Dense Frost",18));
        Button wifi=button("Wi-Fi · Connected",true); wifi.setContentDescription("Wi-Fi active Ice atmosphere"); quick.addView(wifi);
        Button perf=button("Performance · "+profileLabel(),true); perf.setContentDescription("Performance "+profileLabel()); quick.addView(perf);
        page.addView(quick);

        TextView critical=card("CRITICAL SYSTEM · OPAQUE FROST\nHigh-opacity clarity stays separate.",opaque(raised),22);
        critical.setContentDescription("Critical System Opaque Frost non backdrop dependent"); page.addView(critical);

        TextView actionState=label("Action: Ready",14); actionState.setContentDescription("Action state Ready");
        Button action=button("Primary action",false); action.setContentDescription("Primary action");
        action.setOnClickListener(v->{actionState.setText("Action: Complete");actionState.setContentDescription("Action state Complete");});
        page.addView(action); page.addView(actionState);
        page.addView(label("Candidate boundary: emulator optical roles/profiles only; not OEM blur, physical device, TalkBack, production, RC, or Stable acceptance.",12));
        scroll.addView(page); scroll.setContentDescription("Frosted Optical Candidate"); return scroll;
    }

    private Button button(String value,boolean active) {
        Button b=new Button(this); b.setAllCaps(false); b.setText(value); b.setTextSize(15); b.setGravity(Gravity.CENTER_VERTICAL);
        int h=Math.max(active?76:target,target); b.setMinHeight(dp(h)); b.setMinimumHeight(dp(h));
        int bg=active?mix(raised,atmosphere,atmosphereStrength==0f?.16f:.28f):CLEAR_SKY_BLUE;
        b.setTextColor(active?text:COOL_GRAPHITE); b.setBackground(shape(bg,20,active?mix(edge,GLACIER_BLUE,.70f):CRYSTAL_WHITE));
        return b;
    }

    private TextView card(String value,int bg,int radius) {
        TextView v=label(value,15); v.setPadding(dp(16),dp(16),dp(16),dp(16)); v.setBackground(shape(bg,radius,edge)); return v;
    }
    private TextView label(String value,int sp) {
        TextView v=new TextView(this); v.setText(value); v.setTextSize(sp); v.setTextColor(sp>=18?text:secondary); v.setPadding(0,dp(5),0,dp(8)); return v;
    }
    private GradientDrawable environment() {
        int ice=mix(canvas,atmosphere,.08f*atmosphereStrength), crystal=mix(canvas,CRYSTAL_WHITE,.08f*atmosphereStrength);
        return new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{crystal,canvas,ice});
    }
    private GradientDrawable shape(int color,int radius,int stroke) {
        GradientDrawable g=new GradientDrawable(); g.setColor(color); g.setCornerRadius(dp(radius)); g.setStroke(dp(1),stroke); return g;
    }
    private String appearanceLabel(){return "deep-dark".equals(appearance)?"Deep Dark":("dark".equals(appearance)?"Dark":"Light");}
    private String profileLabel(){return "minimal".equals(profile)?"Minimal":("reduced".equals(profile)?"Reduced":"Full");}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private static int alpha(int c,int a){return Color.argb(a,Color.red(c),Color.green(c),Color.blue(c));}
    private static int opaque(int c){return Color.rgb(Color.red(c),Color.green(c),Color.blue(c));}
    private static int mix(int a,int b,float t){
        t=Math.max(0f,Math.min(1f,t));
        return Color.argb(Math.round(Color.alpha(a)*(1-t)+Color.alpha(b)*t),Math.round(Color.red(a)*(1-t)+Color.red(b)*t),
            Math.round(Color.green(a)*(1-t)+Color.green(b)*t),Math.round(Color.blue(a)*(1-t)+Color.blue(b)*t));
    }
}
