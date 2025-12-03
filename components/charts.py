import streamlit as st
import pandas as pd
import io

def render_pie_chart(data, title=""):
    if not data:
        return
    
    df = pd.DataFrame([
        {"Class": name, "Percentage": info.get("percentage", 0), "Color": info.get("color", "#ccc")}
        for name, info in data.items()
    ])
    
    if df.empty:
        return
    
    df = df[df["Percentage"] > 0].sort_values("Percentage", ascending=False)
    
    if df.empty:
        return
    
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = df["Color"].tolist()
    
    def make_autopct(threshold=3):
        def autopct(pct):
            return f'{pct:.1f}%' if pct >= threshold else ''
        return autopct
    
    wedges, texts, autotexts = ax.pie(
        df["Percentage"],
        labels=None,
        colors=colors,
        autopct=make_autopct(3),
        startangle=90,
        pctdistance=0.75,
        labeldistance=1.1,
    )
    
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
        autotext.set_color('white')
    
    centre_circle = plt.Circle((0, 0), 0.55, fc='white')
    fig.gca().add_artist(centre_circle)
    
    legend_labels = [f"{row['Class']} ({row['Percentage']:.1f}%)" for _, row in df.iterrows()]
    ax.legend(wedges, legend_labels, title="Land Cover", loc="center left", 
              bbox_to_anchor=(1, 0.5), fontsize=9, title_fontsize=10)
    
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
    
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def render_bar_chart(data, title="", x_label="", y_label=""):
    if not data:
        return
    
    df = pd.DataFrame([
        {"Class": name, "Percentage": info.get("percentage", 0), "Area": info.get("area_sqkm", 0), "Color": info.get("color", "#ccc")}
        for name, info in data.items()
    ])
    
    if df.empty:
        return
    
    df = df.sort_values("Percentage", ascending=True)
    
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = df["Color"].tolist()
    
    bars = ax.barh(df["Class"], df["Percentage"], color=colors, edgecolor='white')
    
    for bar, pct in zip(bars, df["Percentage"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                f'{pct:.1f}%', va='center', fontsize=9)
    
    ax.set_xlabel(x_label or "Percentage (%)")
    ax.set_ylabel(y_label or "Land Cover Class")
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def render_line_chart(time_series_data, title="", y_label="", show_rolling=True):
    if not time_series_data:
        st.warning("No time series data available.")
        return
    
    df = pd.DataFrame(time_series_data)
    
    if df.empty or "date" not in df.columns:
        st.warning("Invalid time series data format.")
        return
    
    df["date"] = pd.to_datetime(df["date"])
    
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df["date"], df["value"], 'o-', label="Observed", color="#2196F3", markersize=4)
    
    if show_rolling and "rolling_avg" in df.columns:
        ax.plot(df["date"], df["rolling_avg"], '-', label="Rolling Avg", color="#FF9800", linewidth=2)
    
    ax.set_xlabel("Date")
    ax.set_ylabel(y_label or "Value")
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def render_multi_pollutant_chart(time_series_dict, title=""):
    if not time_series_dict:
        st.warning("No time series data available.")
        return
    
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]
    
    for i, (pollutant, data) in enumerate(time_series_dict.items()):
        if data:
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            ax.plot(df["date"], df["value"], 'o-', label=pollutant, 
                   color=colors[i % len(colors)], markersize=3)
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Concentration (normalized)")
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def render_correlation_heatmap(correlations, pollutants, title=""):
    if not correlations:
        st.warning("No correlation data available.")
        return
    
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    
    n = len(pollutants)
    matrix = np.zeros((n, n))
    
    for i, p1 in enumerate(pollutants):
        for j, p2 in enumerate(pollutants):
            val = correlations.get((p1, p2), None)
            matrix[i, j] = val if val is not None else 0
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    im = ax.imshow(matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(pollutants, rotation=45, ha='right')
    ax.set_yticklabels(pollutants)
    
    for i in range(n):
        for j in range(n):
            text = ax.text(j, i, f'{matrix[i, j]:.2f}',
                          ha='center', va='center', color='black', fontsize=10)
    
    plt.colorbar(im, ax=ax, label='Correlation')
    
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def render_radar_chart(data, title=""):
    if not data:
        st.warning("No data for radar chart.")
        return
    
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    
    categories = list(data.keys())
    values = list(data.values())
    
    max_val = max(values) if values else 1
    normalized_values = [v / max_val for v in values]
    
    normalized_values += normalized_values[:1]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    ax.plot(angles, normalized_values, 'o-', linewidth=2, color='#2196F3')
    ax.fill(angles, normalized_values, alpha=0.25, color='#2196F3')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', y=1.08)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def generate_csv_download(df, filename="data.csv"):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def render_download_button(data, filename, label="Download CSV"):
    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )
