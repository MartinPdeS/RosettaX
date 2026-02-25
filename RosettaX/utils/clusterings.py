import numpy as np
import hdbscan
from sklearn.neighbors import KernelDensity
from sklearn.cluster import KMeans


class SigmaThresholdHDBSCAN:
    """
    HDBSCAN clustering with sigma based thresholding.

    Supports 1D or 2D data.

    Optionally merges HDBSCAN clusters down to a requested n_clusters
    using KMeans on cluster centroids.
    """

    # ------------------------------------------------------------
    # Sigma computation
    # ------------------------------------------------------------
    @staticmethod
    def compute_sigma(values, method="robust"):
        v = np.asarray(values)
        if method == "std":
            return np.std(v)
        med = np.median(v)
        mad = np.median(np.abs(v - med))
        return 1.4826 * mad

    # ------------------------------------------------------------
    # Parse "3sigma" or float
    # ------------------------------------------------------------
    @staticmethod
    def parse_threshold(value, sigma):
        if isinstance(value, str) and value.endswith("sigma"):
            k = float(value.replace("sigma", ""))
            return k * sigma
        return float(value)

    # ------------------------------------------------------------
    # KDE based mode estimation
    # ------------------------------------------------------------
    @staticmethod
    def estimate_mode(points, bandwidth=None):
        points = np.asarray(points)
        if len(points) == 0:
            return np.full(points.shape[1], np.nan)

        n, d = points.shape
        if bandwidth is None:
            std = np.std(points, axis=0)
            bandwidth = n ** (-1.0 / (d + 4)) * std.mean()

        kde = KernelDensity(bandwidth=bandwidth).fit(points)
        log_density = kde.score_samples(points)
        return points[np.argmax(log_density)]

    # ------------------------------------------------------------
    # Robust per axis scaling for HDBSCAN
    # ------------------------------------------------------------
    @staticmethod
    def robust_scale(data):
        """
        Robustly scale each column (median and MAD).
        Returns scaled_data, median, scale.
        """
        data = np.asarray(data)
        med = np.median(data, axis=0)
        mad = np.median(np.abs(data - med), axis=0)
        scale = 1.4826 * mad

        zero_mask = scale == 0
        if np.any(zero_mask):
            scale[zero_mask] = np.std(data[:, zero_mask], axis=0) + 1e-12

        scaled = (data - med) / scale
        return scaled, med, scale

    # ------------------------------------------------------------
    # Backward compatible wrapper
    # ------------------------------------------------------------
    def fit(
        self,
        x,
        y=None,
        *,
        n_clusters=None,
        threshold_x=0,
        threshold_y=0,
        sigma_method="robust",
        min_cluster_size=50,
        min_samples=None,
        standardize=True,
        debug=False,
    ):
        x = np.asarray(x)
        if y is None:
            return self.fit_1d(
                x,
                n_clusters=n_clusters,
                threshold_x=threshold_x,
                sigma_method=sigma_method,
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                standardize=standardize,
                debug=debug,
            )
        y = np.asarray(y)
        return self.fit_2d(
            x,
            y,
            n_clusters=n_clusters,
            threshold_x=threshold_x,
            threshold_y=threshold_y,
            sigma_method=sigma_method,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            standardize=standardize,
            debug=debug,
        )

    # ------------------------------------------------------------
    # Shared clustering and summarization core
    # ------------------------------------------------------------
    def _cluster_and_summarize(
        self,
        clean_data,
        *,
        n_clusters,
        min_cluster_size,
        min_samples,
        standardize,
        debug,
    ):
        clean_data = np.asarray(clean_data)

        if standardize:
            scaled_data, med, scale = self.robust_scale(clean_data)
        else:
            scaled_data = clean_data

        if min_samples is None:
            min_samples = min_cluster_size

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
        )
        clusterer.fit(scaled_data)

        labels_raw = clusterer.labels_  # -1 is noise
        unique_raw = [k for k in np.unique(labels_raw) if k >= 0]

        if len(unique_raw) == 0:
            if debug:
                print(
                    "HDBSCAN found no clusters; consider lowering "
                    "min_cluster_size or min_samples."
                )
            labels_raw = np.zeros(len(clean_data), dtype=int)
            unique_raw = [0]

        if n_clusters is None:
            final_labels = labels_raw
            used_labels = [k for k in np.unique(final_labels) if k >= 0]
        else:
            core_mask = labels_raw >= 0
            core_labels = labels_raw[core_mask]
            core_data = clean_data[core_mask]

            unique_raw = np.unique(core_labels)

            if len(unique_raw) == 0:
                core_mask = np.ones(len(clean_data), dtype=bool)
                core_data = clean_data
                core_labels = np.zeros(len(clean_data), dtype=int)
                unique_raw = np.array([0])

            centroids = np.array(
                [core_data[core_labels == k].mean(axis=0) for k in unique_raw]
            )

            if len(unique_raw) <= n_clusters:
                label_map = {old: i for i, old in enumerate(unique_raw)}
            else:
                km = KMeans(n_clusters=n_clusters, n_init=20)
                km.fit(centroids)
                label_map = {old: new for old, new in zip(unique_raw, km.labels_)}

            final_labels = np.full_like(labels_raw, fill_value=-1)
            for idx, lab in enumerate(labels_raw):
                if lab >= 0:
                    final_labels[idx] = label_map[lab]

            used_labels = sorted([k for k in np.unique(final_labels) if k >= 0])

        K = len(used_labels)
        dim = clean_data.shape[1]
        means = np.zeros((K, dim))
        modes = np.zeros((K, dim))

        for i, k in enumerate(used_labels):
            pts = clean_data[final_labels == k]
            means[i] = pts.mean(axis=0)
            modes[i] = self.estimate_mode(pts)

        return final_labels, means, modes, used_labels

    # ------------------------------------------------------------
    # 1D fit
    # ------------------------------------------------------------
    def fit_1d(
        self,
        x,
        *,
        n_clusters=None,
        threshold_x=0,
        sigma_method="robust",
        min_cluster_size=50,
        min_samples=None,
        standardize=True,
        debug=False,
    ):
        x = np.asarray(x)

        sigma_x = self.compute_sigma(x, sigma_method)
        tx = self.parse_threshold(threshold_x, sigma_x)

        mask = x > tx
        x_clean = x[mask]
        clean_data = x_clean.reshape(-1, 1)

        ax_thr = None
        ax_clu = None

        if debug:
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec

            fig = plt.figure(figsize=(10, 6))
            gs = gridspec.GridSpec(2, 1)
            ax_thr = fig.add_subplot(gs[0])
            ax_clu = fig.add_subplot(gs[1])

            ax_thr.hist(x, bins=200, color="lightgray", alpha=0.5, label="Original")
            ax_thr.hist(x_clean, bins=200, color="blue", alpha=0.6, label="Kept")
            ax_thr.axvline(tx, color="red", linestyle="--", linewidth=2)
            ax_thr.set_title("1D sigma thresholding")
            ax_thr.legend()

        final_labels, means, modes, used_labels = self._cluster_and_summarize(
            clean_data,
            n_clusters=n_clusters,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            standardize=standardize,
            debug=debug,
        )

        if debug:
            import matplotlib.pyplot as plt

            cmap = plt.get_cmap("tab10")
            for i, k in enumerate(used_labels):
                pts = clean_data[final_labels == k, 0]
                ax_clu.hist(
                    pts,
                    bins=200,
                    alpha=0.7,
                    color=cmap(i),
                    label=f"Cluster {k}",
                )

            for i in range(len(used_labels)):
                ax_clu.axvline(means[i, 0], color="black", linestyle="--", linewidth=2)
                ax_clu.axvline(modes[i, 0], color="red", linewidth=2)

            ax_clu.set_title("HDBSCAN clustering (1D)")
            ax_clu.legend()
            plt.tight_layout()
            plt.show()

        return final_labels, means, modes, clean_data, mask

    # ------------------------------------------------------------
    # 2D fit
    # ------------------------------------------------------------
    def fit_2d(
        self,
        x,
        y,
        *,
        n_clusters=None,
        threshold_x=0,
        threshold_y=0,
        sigma_method="robust",
        min_cluster_size=50,
        min_samples=None,
        standardize=True,
        debug=False,
    ):
        x = np.asarray(x)
        y = np.asarray(y)

        sigma_x = self.compute_sigma(x, sigma_method)
        tx = self.parse_threshold(threshold_x, sigma_x)

        sigma_y = self.compute_sigma(y, sigma_method)
        ty = self.parse_threshold(threshold_y, sigma_y)

        mask = (x > tx) & (y > ty)
        x_clean = x[mask]
        y_clean = y[mask]
        clean_data = np.column_stack([x_clean, y_clean])

        ax_thr = None
        ax_clu = None

        if debug:
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec

            fig = plt.figure(figsize=(14, 6))
            gs = gridspec.GridSpec(1, 2)
            ax_thr = fig.add_subplot(gs[0])
            ax_clu = fig.add_subplot(gs[1])

            ax_thr.scatter(x, y, c="lightgray", s=3, alpha=0.3)
            ax_thr.scatter(x_clean, y_clean, c="blue", s=5, alpha=0.8)
            ax_thr.axvline(tx, color="red", linestyle="--", linewidth=2)
            ax_thr.axhline(ty, color="red", linestyle="--", linewidth=2)
            ax_thr.set_title("2D sigma thresholding")

        final_labels, means, modes, used_labels = self._cluster_and_summarize(
            clean_data,
            n_clusters=n_clusters,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            standardize=standardize,
            debug=debug,
        )

        if debug:
            import matplotlib.pyplot as plt

            cmap = plt.get_cmap("tab10")

            noise_mask = final_labels < 0
            if np.any(noise_mask):
                ax_clu.scatter(
                    clean_data[noise_mask, 0],
                    clean_data[noise_mask, 1],
                    s=8,
                    c="lightgray",
                    alpha=0.4,
                    label="Noise",
                )

            for i, k in enumerate(used_labels):
                pts = clean_data[final_labels == k]
                ax_clu.scatter(
                    pts[:, 0],
                    pts[:, 1],
                    s=10,
                    color=cmap(i),
                    alpha=0.9,
                    label=f"Cluster {k}",
                )

            ax_clu.scatter(
                means[:, 0],
                means[:, 1],
                c="black",
                s=200,
                marker="x",
                linewidths=2,
                label="Means",
            )
            ax_clu.scatter(
                modes[:, 0],
                modes[:, 1],
                c="red",
                s=220,
                marker="*",
                label="Modes",
            )

            ax_clu.set_title("HDBSCAN clustering (2D)")
            ax_clu.legend()
            plt.tight_layout()
            plt.show()

        return final_labels, means, modes, clean_data, mask
