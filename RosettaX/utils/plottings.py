import numpy as np
import matplotlib.pyplot as plt

def plot_2d_clusters(
    data_clean,
    labels,
    means,
    modes,
    *,
    x_original=None,
    y_original=None,
    gridsize=200,
    cmap="tab10",
    background_cmap="gray_r",
    figsize=(8, 8),
    scatter_size=10,
):
    """
    Plot 2D clusters obtained from a thresholded GMM or DBSCAN.

    Parameters
    ----------
    data_clean : ndarray of shape (N, 2)
        Cleaned 2D data used for clustering.

    labels : ndarray of shape (N,)
        Cluster labels for cleaned data.

    means : ndarray of shape (K, 2)
        Estimated cluster centers (GMM means).

    modes : ndarray of shape (K, 2)
        KDE-derived cluster modes.

    x_original, y_original : ndarray or None
        Full original dataset to draw background density (optional).

    gridsize : int
        Resolution of hexbin background.

    cmap : str
        Colormap for the cluster points.

    background_cmap : str
        Colormap for the background hexbin.

    scatter_size : int
        Size of cluster scatter points.

    Returns
    -------
    fig, ax : matplotlib figure and axis
    """

    import numpy as np
    import matplotlib.pyplot as plt

    data_clean = np.asarray(data_clean)
    x = data_clean[:, 0]
    y = data_clean[:, 1]

    fig, ax = plt.subplots(figsize=figsize)

    # ---------------------------------------------------------
    # Background hexbin (optional)
    # ---------------------------------------------------------
    if x_original is not None and y_original is not None:
        ax.hexbin(
            x_original,
            y_original,
            gridsize=gridsize,
            mincnt=1,
            cmap=background_cmap,
            bins="log",
            alpha=0.8,
        )

    # ---------------------------------------------------------
    # Cluster points
    # ---------------------------------------------------------
    unique_labels = np.unique(labels)
    cmap_obj = plt.get_cmap(cmap)

    for i, lab in enumerate(unique_labels):
        mask = labels == lab
        ax.scatter(
            x[mask],
            y[mask],
            s=scatter_size,
            color=cmap_obj(i),
            alpha=0.9,
            label=f"Cluster {lab}",
        )

    # ---------------------------------------------------------
    # Plot means
    # ---------------------------------------------------------
    if means is not None and len(means) > 0:
        ax.scatter(
            means[:, 0],
            means[:, 1],
            s=200,
            color="black",
            marker="x",
            linewidths=2,
            label="Means",
        )

    # ---------------------------------------------------------
    # Plot modes
    # ---------------------------------------------------------
    if modes is not None and len(modes) > 0:
        ax.scatter(
            modes[:, 0],
            modes[:, 1],
            s=260,
            color="red",
            marker="*",
            label="Modes",
        )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()
    return fig, ax



def plot_1d_clusters(
    x_clean,
    labels,
    means,
    modes,
    *,
    x_original=None,
    bins=200,
    log_scale=False,
    figsize=(8, 5),
    cmap="tab10",
):
    """
    Plot 1D clusters obtained from a thresholded GMM.

    Parameters
    ----------
    x_clean : ndarray
        Cleaned data used for clustering.

    labels : ndarray
        Cluster labels for x_clean.

    means : ndarray of shape (K, 1)
        Gaussian means from GMM.

    modes : ndarray of shape (K, 1)
        KDE-derived modes.

    x_original : ndarray or None
        Raw data for background histogram.

    bins : int
        Number of histogram bins.

    log_scale : bool
        If True, plot in log(x) space.

    cmap : str
        Matplotlib colormap name.

    Returns
    -------
    fig, ax : matplotlib figure and axis
    """
    import matplotlib.pyplot as plt
    import numpy as np

    x_clean = np.asarray(x_clean)

    # Prepare plotting values
    if log_scale:
        # filter non-positive values
        x_plot = np.log(x_clean[x_clean > 0])

        if x_original is not None:
            x_bg = np.log(x_original[x_original > 0])
        else:
            x_bg = None

        means_plot = np.log(means[:, 0])
        modes_plot = np.log(modes[:, 0])
        xlabel = "log(x)"
    else:
        x_plot = x_clean
        x_bg = x_original
        means_plot = means[:, 0]
        modes_plot = modes[:, 0]
        xlabel = "x"

    fig, ax = plt.subplots(figsize=figsize)

    # Background histogram
    if x_bg is not None:
        ax.hist(
            x_bg,
            bins=bins,
            color="lightgray",
            alpha=0.4,
            label="Background",
        )

    # Plot clusters
    unique_labels = np.unique(labels)
    cmap_obj = plt.get_cmap(cmap)

    for i, lab in enumerate(unique_labels):
        xc = x_plot[labels == lab]
        ax.hist(
            xc,
            bins=bins,
            color=cmap_obj(i),
            alpha=0.7,
            label=f"Cluster {lab}",
        )

    # Plot means (black dashed)
    ax.vlines(
        means_plot,
        ymin=0,
        ymax=ax.get_ylim()[1],
        color="black",
        linestyle="--",
        linewidth=2,
        label="Means",
    )

    # Plot modes (red solid)
    ax.vlines(
        modes_plot,
        ymin=0,
        ymax=ax.get_ylim()[1],
        color="red",
        linestyle="-",
        linewidth=2,
        label="Modes",
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Counts")
    ax.legend()

    return fig, ax

