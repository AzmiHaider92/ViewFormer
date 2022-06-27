import tensorflow as tf
from tensorflow.python.util import nest
from viewformer.utils import geometry_tf as geometry


def _with_flat_batch(flat_batch_fn):
    def fn(x, *args, **kwargs):
        shape = tf.shape(x)
        flat_batch_x = tf.reshape(x, tf.concat([[-1], shape[-3:]], axis=0))
        flat_batch_r = flat_batch_fn(flat_batch_x, *args, **kwargs)
        r = nest.map_structure(lambda x: tf.reshape(x, tf.concat([shape[:-3], x.shape[1:]], axis=0)),
                               flat_batch_r)
        return r
    return fn


def ssim(X, Y, K1=0.01, K2=0.03, win_size=7,
                          data_range=1.0, use_sample_covariance=True):
    """
    Structural SIMilarity (SSIM) index between two images
    Args:
        X: A tensor of shape `[..., in_height, in_width, in_channels]`.
        Y: A tensor of shape `[..., in_height, in_width, in_channels]`.
    Returns:
        The SSIM between images X and Y.
    Reference:
        https://github.com/scikit-image/scikit-image/blob/master/skimage/measure/_structural_similarity.py
    Broadcasting is supported.
    """
    X = tf.convert_to_tensor(X)
    Y = tf.convert_to_tensor(Y)

    ndim = 2  # number of spatial dimensions
    nch = tf.shape(X)[-1]

    filter_func = _with_flat_batch(tf.nn.depthwise_conv2d)
    kernel = tf.cast(tf.fill([win_size, win_size, nch, 1], 1 / win_size ** 2), X.dtype)
    filter_args = {'filter': kernel, 'strides': [1] * 4, 'padding': 'VALID'}

    NP = win_size ** ndim

    # filter has already normalized by NP
    if use_sample_covariance:
        cov_norm = NP / (NP - 1)  # sample covariance
    else:
        cov_norm = 1.0  # population covariance to match Wang et. al. 2004

    # compute means
    ux = filter_func(X, **filter_args)
    uy = filter_func(Y, **filter_args)

    # compute variances and covariances
    uxx = filter_func(X * X, **filter_args)
    uyy = filter_func(Y * Y, **filter_args)
    uxy = filter_func(X * Y, **filter_args)
    vx = cov_norm * (uxx - ux * ux)
    vy = cov_norm * (uyy - uy * uy)
    vxy = cov_norm * (uxy - ux * uy)

    R = data_range
    C1 = (K1 * R) ** 2
    C2 = (K2 * R) ** 2

    A1, A2, B1, B2 = ((2 * ux * uy + C1,
                       2 * vxy + C2,
                       ux ** 2 + uy ** 2 + C1,
                       vx + vy + C2))
    D = B1 * B2
    S = (A1 * A2) / D

    ssim = tf.reduce_mean(S, axis=[-3, -2, -1])
    return ssim


class AllowNanMean(tf.metrics.Mean):
    def __init__(self, name, dtype='float32', allow_nan=True, **kwargs):
        super().__init__(name=name, dtype=dtype, **kwargs)
        self.allow_nan = allow_nan

    def update_state(self, values, sample_weight=None):
        if self.allow_nan:
            values = tf.reshape(values, (-1,))
            if sample_weight is None:
                sample_weight = tf.ones_like(values)
            values = tf.where(tf.math.is_nan(values), tf.zeros_like(values), values)
            sample_weight = sample_weight * (1. - tf.cast(tf.math.is_nan(values), sample_weight.dtype))
        super().update_state(values, sample_weight)


class CameraPositionError(AllowNanMean):
    def __init__(self, name='pose_pos_err', **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, x1, x2):
        super().update_state(tf.norm(x1[..., :3] - x2[..., :3], ord=2, axis=-1))


class CameraOrientationError(AllowNanMean):
    def __init__(self, name='pose_ori_err', **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, x1, x2):
        x1 = geometry.quaternion_normalize(x1[..., 3:])
        x2 = geometry.quaternion_normalize(x2[..., 3:])

        # We use sin method because it is more stable around
        # the point, where the rotation is 0
        diff = geometry.quaternion_multiply(x1, geometry.quaternion_conjugate(x2))
        theta = 2 * tf.asin(tf.linalg.norm(diff[..., 1:], axis=-1))
        super().update_state(theta)


class Median(tf.metrics.Metric):
    def __init__(self, name='median', **kwargs):
        super().__init__(name=name, **kwargs)
        self._store = None

    def update_state(self, values):
        values = tf.convert_to_tensor(values)
        values = tf.reshape(values, (-1,))
        values = tf.cast(values, self.dtype)
        if self._store is None:
            self._store = values
        else:
            self._store = tf.concat((self._store, values), 0)

    def reset_states(self):
        self._store = None

    def result(self):
        # Compute median
        vals = tf.sort(self._store)
        if len(vals) % 2 == 1:
            return vals[(len(vals) - 1) // 2]
        else:
            return 0.5 * (vals[int(len(vals) // 2 - 1)] + vals[int(len(vals) // 2)])


class CameraPositionMedian(Median):
    def __init__(self, name='pose_pos_median', **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, x1, x2):
        super().update_state(tf.norm(x1[..., :3] - x2[..., :3], ord=2, axis=-1))


class CameraOrientationMedian(Median):
    def __init__(self, name='pose_ori_median', **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, x1, x2):
        x1 = geometry.quaternion_normalize(x1[..., 3:])
        x2 = geometry.quaternion_normalize(x2[..., 3:])

        # We use sin method because it is more stable around
        # the point, where the rotation is 0
        diff = geometry.quaternion_multiply(x1, geometry.quaternion_conjugate(x2))
        theta = 2 * tf.asin(tf.linalg.norm(diff[..., 1:], axis=-1))
        super().update_state(theta)


class ImageRMSE(tf.keras.metrics.Mean):
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, gt_images, images):
        gt_images = tf.image.convert_image_dtype(gt_images, 'float32') * 255.
        images = tf.image.convert_image_dtype(images, 'float32') * 255.
        val = tf.reduce_mean(tf.math.squared_difference(gt_images, images), (-1, -2, -3))
        val = tf.math.sqrt(val)
        super().update_state(val)


class SSIMMetric(tf.keras.metrics.Mean):
    def __init__(self, name='ssim', **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, gt_images, images):
        gt_images = tf.image.convert_image_dtype(gt_images, 'float32')
        images = tf.image.convert_image_dtype(images, 'float32')
        val = ssim(gt_images, images, 1)
        super().update_state(val)


class PSNRMetric(tf.keras.metrics.Mean):
    def __init__(self, name='psnr', **kwargs):
        super().__init__(name=name, **kwargs)

    def update_state(self, gt_images, images):
        gt_images = tf.image.convert_image_dtype(gt_images, 'float32')
        images = tf.image.convert_image_dtype(images, 'float32')
        val = tf.image.psnr(gt_images, images, 1)
        super().update_state(val)


from six.moves import urllib
import os
import sys
_URL = 'http://rail.eecs.berkeley.edu/models/lpips'
def _download(url, output_dir):
    """Downloads the `url` file into `output_dir`.

    Modified from https://github.com/tensorflow/models/blob/master/research/slim/datasets/dataset_utils.py
    """
    filename = url.split('/')[-1]
    filepath = os.path.join(output_dir, filename)

    def _progress(count, block_size, total_size):
        sys.stdout.write('\r>> Downloading %s %.1f%%' % (
            filename, float(count * block_size) / float(total_size) * 100.0))
        sys.stdout.flush()
    
    filepath, _ = urllib.request.urlretrieve(url, filepath, _progress)
    print()
    statinfo = os.stat(filepath)
    print('Successfully downloaded', filename, statinfo.st_size, 'bytes.')


def lpips_tf(input0, input1, model='net-lin', net='alex', version=0.1):
    """
    Learned Perceptual Image Patch Similarity (LPIPS) metric.

    Args:
        input0: An image tensor of shape `[..., height, width, channels]`,
            with values in [0, 1].
        input1: An image tensor of shape `[..., height, width, channels]`,
            with values in [0, 1].

    Returns:
        The Learned Perceptual Image Patch Similarity (LPIPS) distance.

    Reference:
        Richard Zhang, Phillip Isola, Alexei A. Efros, Eli Shechtman, Oliver Wang.
        The Unreasonable Effectiveness of Deep Features as a Perceptual Metric.
        In CVPR, 2018.
    """
    # flatten the leading dimensions
    batch_shape = tf.shape(input0)[:-3]
    input0 = tf.reshape(input0, tf.concat([[-1], tf.shape(input0)[-3:]], axis=0))
    input1 = tf.reshape(input1, tf.concat([[-1], tf.shape(input1)[-3:]], axis=0))
    # NHWC to NCHW
    input0 = tf.transpose(input0, [0, 3, 1, 2])
    input1 = tf.transpose(input1, [0, 3, 1, 2])
    # normalize to [-1, 1]
    input0 = input0 * 2.0 - 1.0
    input1 = input1 * 2.0 - 1.0

    input0_name, input1_name = '0:0', '1:0'

    default_graph = tf.compat.v1.get_default_graph()
    producer_version = default_graph.graph_def_versions.producer
    
    curr_dir = os.getcwd()
    cache_dir = os.path.join(curr_dir, 'lpips')
    os.makedirs(cache_dir, exist_ok=True)
    # files to try. try a specific producer version, but fallback to the version-less version (latest).
    pb_fnames = [
        '%s_%s_v%s_%d.pb' % (model, net, version, producer_version),
        '%s_%s_v%s.pb' % (model, net, version),
    ]    

    for pb_fname in pb_fnames:
        if not os.path.isfile(os.path.join(cache_dir, pb_fname)):
            try:
                _download(os.path.join(_URL, pb_fname), cache_dir)
            except urllib.error.HTTPError:
                pass
        if os.path.isfile(os.path.join(cache_dir, pb_fname)):
            break

    with open(os.path.join(cache_dir, pb_fname), 'rb') as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.compat.v1.import_graph_def(graph_def,
                                input_map={input0_name: input0, input1_name: input1})
        distance, = default_graph.get_operations()[-1].outputs

    if distance.shape.ndims == 4:
        distance = tf.squeeze(distance, axis=[-3, -2, -1])
    # reshape the leading dimensions
    distance = tf.reshape(distance, batch_shape)
    return distance


class LPIPSMetric(tf.keras.metrics.Mean):
    _lpips_pool = dict()

    def __init__(self, net='vgg', name=None, **kwargs):
        #from viewformer.models.utils import lpips
        import lpips
        if name is None:
            name = f'lpips-{net}'
        super().__init__(name=name, **kwargs)
        if net not in self._lpips_pool:
            self._lpips_pool[net] = lpips.LPIPS(net)
        self.lpips = self._lpips_pool[net]
    
    @tf.function
    def update_state(self, gt_images, images):
        gt_images = tf.image.convert_image_dtype(gt_images, 'float32')
        images = tf.image.convert_image_dtype(images, 'float32')
        val = lpips_tf(input0=gt_images,input1=images, net='vgg')
        print(val)
        super().update_state(val)
