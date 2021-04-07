import numpy as np
from .utils import arrayCompat, asarray


class Quaternion(np.ndarray):
    """ A single quaternion object stored in xyzw order (scalar last) """
    def __new__(cls, input_array=None):
        if input_array is None:
            ary = np.zeros(4)
            ary[3] = 1
        else:
            ary = np.asarray(input_array, dtype=float)
        if ary.size != 4:
            raise ValueError(
                "Initializer for Vector{0} must be of length {0}".format(4)
            )
        return ary.view(cls)

    @classmethod
    def fromComponents(cls, x, y, z, w):
        """ Build a quaternion from individual components

        Parameters
        ----------
        x: float
            The X Component of the quaternion
        y: float
            The Y Component of the quaternion
        z: float
            The Z Component of the quaternion
        w: float
            The W Component of the quaternion

        Returns
        -------
        Quaternion
            The resulting quaternion
        """
        return cls([x, y, z, w])

    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, val):
        self[0] = val

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, val):
        self[1] = val

    @property
    def z(self):
        return self[2]

    @z.setter
    def z(self, val):
        self[2] = val

    @property
    def w(self):
        return self[3]

    @w.setter
    def w(self, val):
        self[3] = val

    @classmethod
    def getReturnType(cls, shape):
        """ Get the type for any return values based on the shape of the return value
        This is mainly for internal use

        Parameters
        ----------
        shape: tuple
            The shape of the output

        Returns
        -------
        type
            The type that the output should have
        """

        if not shape:
            return None
        if len(shape) == 1:
            if shape[0] == 4:
                return cls
        elif len(shape) == 2:
            # This could happen with fancy indexing
            if shape[-1] == 4:
                return QuaternionArray

        return np.ndarray

    def __getitem__(self, idx):
        ret = super(Quaternion, self).__getitem__(idx)
        typ = self.getReturnType(ret.shape)
        if typ is None:
            return ret
        return ret.view(typ)

    def asArray(self):
        """ Return the array type of this object

        Returns
        -------
        ArrayType:
            The current object up-cast into a length-1 array
        """
        return self[None, ...]

    def asNdArray(self):
        """ Return this object as a regular numpy array

        Returns
        -------
        ndarray:
            The current object as a numpy array
        """
        return self.view(np.ndarray)

    def lengthSquared(self):
        """ Return the squared length of the quaternion

        Returns
        -------
        float:
            The squared length of the quaternion
        """
        return self.asArray().lengthSquared()[0]

    def length(self):
        """ Return the length of the quaternion

        Returns
        -------
        float:
            The length of the quaternion
        """
        return np.sqrt(self.lengthSquared())

    def normal(self):
        """ Return the normalized quaternion

        Returns
        -------
        VectorN:
            The normalized quaternion
        """
        return self.asArray().normal()[0]

    def normalize(self):
        """ Normalize the quaternion in-place """
        self /= self.length()

    def __mul__(self, other):
        other = asarray(other)
        if isinstance(other, Quaternion):
            return QuaternionArray.quatquatProduct(self[None, ...], other[None, ...])[0]
        elif isinstance(other, QuaternionArray):
            return QuaternionArray.quatquatProduct(self[None, ...], other)

        from .vectorN import VectorN, VectorNArray
        if isinstance(other, (VectorN, VectorNArray)):
            raise NotImplementedError(
                "Vectors must always be on the left side of the multiplication"
            )
        return super(Quaternion, self).__mul__(other)

    def asMatrix(self):
        """ Convert the quaternion to a 3x3 matrix

        Returns
        -------
        Matrix3:
            The orientation as a matrix
        """
        return self[None, ...].asMatrixArray()[0]

    def asEuler(self, order="xyz", degrees=False):
        """ Convert the quaternion to an Euler rotation

        Parameters
        ----------
        order: str, optional
            The order in which the axis rotations are applied
            It must be one of these options ['xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyz']
            Defaults to 'xyz'
        degrees: bool, optional
            Whether the angles are given in degrees or radians. Defaults to False (radians)

        Returns
        -------
        Euler:
            The converted orientation
        """
        return self[None, ...].asEulerArray(order=order, degrees=degrees)[0]

    @staticmethod
    def lookAt(look, up, axis="xy"):
        """ Alternate constructor to create a quaternion looking at a point
        and twisted with the given up value
        Think of the quaternion resting at origin

        Parameters
        ----------
        look: iterable
            A length-3 vector that the primary axis will be pointed at
        up: iterable
            A length-3 vector that the secondary axis will be pointed at
        axis: str, optional
            Define the primary and secondary axes. Must be one of these options
            ['xy', 'xz', 'yx', 'yz', 'zx', 'zy']
        """
        from .matrixN import MatrixNArray
        mats = MatrixNArray.lookAts(look, up, axis=axis)
        return mats.asQuaternionArray()[0]

    @classmethod
    def axisAngle(cls, axis, angle, degrees=False):
        """ An alternate constructor to build a quaternion from an axis and angle

        Arguments
        ---------
        axis: Vector3
            The axes for the axis angle
        angle: iterable
            An angle per axis
        degrees: bool, optional
            If true, then assume the angles are in degrees instead of radians
            Defaults to False
        """
        axis = asarray(axis)
        return QuaternionArray.axisAngle(axis[None, ...], [angle], degrees=degrees)[0]


class QuaternionArray(np.ndarray):
    """ An array of Quaternion objects """

    def __new__(cls, input_array=None):
        if input_array is None:
            input_array = np.array([])
        ary = np.asarray(input_array, dtype=float)
        ary = ary.reshape((-1, 4))
        return ary.view(cls)

    @classmethod
    def fromComponentArrays(cls, x, y, z, w):
        """ Build a quaternion array from individual component arrays
        The arrays must have the same length

        Parameters
        ----------
        x: array
            The array of X components of the quaternions
        y: array
            The array of Y components of the quaternions
        z: array
            The array of Z components of the quaternions
        w: array
            The array of W components of the quaternions

        Returns
        -------
        QuaternionArray
            The resulting quaternion array
        """

        ret = np.array([x, y, z, w]).T
        return cls(ret)

    @property
    def x(self):
        return self[:, 0]

    @x.setter
    def x(self, val):
        self[:, 0] = val

    @property
    def y(self):
        return self[:, 1]

    @y.setter
    def y(self, val):
        self[:, 1] = val

    @property
    def z(self):
        return self[:, 2]

    @z.setter
    def z(self, val):
        self[:, 2] = val

    @property
    def w(self):
        return self[:, 3]

    @w.setter
    def w(self, val):
        self[:, 3] = val

    @classmethod
    def getReturnType(cls, shape):
        """ Get the type for any return values based on the shape of the return value
        This is mainly for internal use

        Parameters
        ----------
        shape: tuple
            The shape of the output

        Returns
        -------
        type
            The type that the output should have
        """
        if not shape:
            return None
        if len(shape) == 2:
            if shape[1] == 4:
                return cls
        elif len(shape) == 1:
            if shape[0] == 4:
                return Quaternion
        return np.ndarray

    def __getitem__(self, idx):
        ret = super(QuaternionArray, self).__getitem__(idx)
        # If we're getting columns from the array
        # Then we expect arrays back, not math3d types
        if isinstance(idx, tuple):
            # If we're getting multiple indices And the second index isn't a ":"
            # Then we're getting columns, and therefore want an ndarray
            if len(idx) > 1 and idx[1] != slice(None, None, None):
                return ret.view(np.ndarray)
        typ = self.getReturnType(ret.shape)
        if typ is None:
            return ret
        return ret.view(typ)

    def lengthSquared(self):
        """ Return the squared length of each quaternion

        Returns
        -------
        np.ndarray:
            The squared lengths of the quaternions
        """
        return np.einsum("...ij,...ij->...i", self, self)

    def length(self):
        """ Return the length of each quaternion

        Returns
        -------
        np.ndarray:
            The lengths of the quaternions
        """
        return np.sqrt(self.lengthSquared())

    def normal(self):
        """ Return the normalized quaternions

        Returns
        -------
        QuaternionArray:
            The normalized quaternions
        """
        return self / self.length()[..., None]

    def normalize(self):
        """ Normalize the quaternions in-place """
        self /= self.length()[..., None]

    @classmethod
    def zeros(cls, length):
        """ Alternate constructor to build an array of quaternions that are all zero

        Parameters
        ----------
        length: int
            The number of matrices to build
        """
        return cls(np.zeros((length, 4)))

    def appended(self, value):
        """ Return a copy of the array with the value appended
        Euler and Matrix types will be converted to Quaternions
        All other types will be appended as-is

        Parameters
        ----------
        value: iterable
            An iterable to be appended as-is to the end of this array
        """
        newShp = list(self.shape)
        newShp[0] += 1
        ret = np.resize(self, newShp).view(type(self))

        from .euler import Euler
        from .matrixN import MatrixN
        if isinstance(value, (Euler, MatrixN)):
            value = value.asQuaternion()

        ret[-1] = value
        return ret

    def extended(self, value):
        """ Return a copy of the array extended with the given values
        Euler and Matrix types will be converted to Quaternions
        All other types will be appended as-is

        Parameters
        ----------
        value: iterable
            An iterable to be appended as-is to the end of this array
        """
        newShp = list(self.shape)
        newShp[0] += len(value)
        ret = np.resize(self, newShp).view(type(self))

        from .euler import EulerArray
        from .matrixN import MatrixNArray
        if isinstance(value, (EulerArray, MatrixNArray)):
            value = value.asQuaternionArray()

        ret[-len(value):] = value
        return ret

    @classmethod
    def alignedRotations(cls, axisName, angles, degrees=False):
        """ An alternate constructor to build a quaternion from a basis vector and angle

        Arguments
        ---------
        axisName: str
            The name of the axis to rotate around: x, y, or z
        angles: iterable
            The angles to rotate around the named axes
        degrees: bool, optional
            If true, then assume the angles are in degrees instead of radians
            Defaults to False
        """
        # where axisName is in 'xyz'
        angles = np.asarray(angles, dtype=float)
        if degrees:
            angles = np.deg2rad(angles)
        ind = "xyz".index(axisName.lower())
        ret = cls.zeros(len(angles))
        ret[:, 3] = np.cos(angles / 2)
        ret[:, ind] = np.sin(angles / 2)
        return ret

    @classmethod
    def axisAngle(cls, axes, angles, degrees=False):
        """ An alternate constructor to build a quaternion from an axis and angle

        Arguments
        ---------
        axes: Vector3Array
            The axes for the axis angle
        angles: iterable
            An angle per axis
        degrees: bool, optional
            If true, then assume the angles are in degrees instead of radians
            Defaults to False
        """
        axes = arrayCompat(axes)
        angles = np.asarray(angles)

        if degrees:
            angles = np.deg2rad(angles)
        sins = np.sin(angles)
        ret = cls.zeros(len(axes))

        ret[:, :3] = axes * sins[:, None]
        ret[:, 3] = np.cos(angles)
        return ret

    @classmethod
    def quatquatProduct(cls, p, q):
        """ A multiplication of two quaternions
        You shouldn't be calling this directly
        It provides no checks for correct inputs
        """
        # This assumes the arrays are shaped correctly
        p, q = arrayCompat(p, q)
        prod = np.empty((max(p.shape[0], q.shape[0]), 4))
        prod[:, 3] = p[:, 3] * q[:, 3] - np.sum(p[:, :3] * q[:, :3], axis=1)
        prod[:, :3] = (
            p[:, None, 3] * q[:, :3]
            + q[:, None, 3] * p[:, :3]
            + np.cross(p[:, :3], q[:, :3])
        )
        return cls(prod)

    @staticmethod
    def vectorquatproduct(v, q):
        """ A multiplication of a vectorArray and a quaternionArray
        You shouldn't be calling this directly
        It provides no checks for correct inputs
        """
        # This assumes the arrays are shaped correctly
        v, q = arrayCompat(v, q)
        qvec = q[:, :3]
        uv = np.cross(qvec, v)
        uuv = np.cross(qvec, uv)
        uv *= 2 * q[:, 3]
        uuv *= 2
        return v + uv + uuv

    def asMatrixArray(self):
        """ Convert the quaternion array to a 3x3 matrix array

        Returns
        -------
        Matrix3Array
            The array of orientations
        """

        from .matrixN import Matrix3Array
        x = self[:, 0]
        y = self[:, 1]
        z = self[:, 2]
        w = self[:, 3]

        xx = x * x
        xy = x * y
        xz = x * z
        xw = x * w

        yy = y * y
        yz = y * z
        yw = y * w

        zz = z * z
        zw = z * w

        num_rotations = len(self)
        mats = Matrix3Array.zeros(num_rotations)

        mats[:, 0, 0] = 1 - 2 * (yy + zz)
        mats[:, 0, 1] = 2 * (xy - zw)
        mats[:, 0, 2] = 2 * (xz + yw)

        mats[:, 1, 0] = 2 * (xy + zw)
        mats[:, 1, 1] = 1 - 2 * (xx + zz)
        mats[:, 1, 2] = 2 * (yz - xw)

        mats[:, 2, 0] = 2 * (xz - yw)
        mats[:, 2, 1] = 2 * (yz + xw)
        mats[:, 2, 2] = 1 - 2 * (xx + yy)

        return mats

    def asEulerArray(self, order="xyz", degrees=False):
        """ Convert the quaternion to an array of Euler rotations

        Parameters
        ----------
        order: str, optional
            The order in which the axis rotations are applied
            It must be one of these options ['xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyz']
            Defaults to 'xyz'
        degrees: bool, optional
            Whether the angles are given in degrees or radians. Defaults to False (radians)

        Returns
        -------
        EulerArray:
            The converted orientation Array
        """
        m = self.asMatrixArray()
        return m.asEulerArray(order=order, degrees=degrees)

    def asNdArray(self):
        """ Return this object as a regular numpy array

        Returns
        -------
        ndarray:
            The current object as a numpy array
        """
        return self.view(np.ndarray)

    def __mul__(self, other):
        other = arrayCompat(other)
        if isinstance(other, QuaternionArray):
            return self.quatquatProduct(self, other)

        from .vectorN import VectorN, VectorNArray

        if isinstance(other, (VectorN, VectorNArray)):
            raise NotImplementedError(
                "Vectors must always be on the left side of the multiplication"
            )

        return super(QuaternionArray, self).__mul__(other)

    @staticmethod
    def lookAts(looks, ups, axis="xy"):
        """ An alternate constructor to look along the look-vectors, oriented to the up-vectors

        Parameters
        ----------
        looks: Vector3Array
            The pointing directions of the look axis
        ups: Vector3Array
            The pointing directions of the up axis
        axis: string
            The axes to align to the look and up vectors (ie: 'xy', 'yz', '-zy', 'x-z')

        Returns
        -------
        QuaternionArray:
            The looking matrices
        """
        from .matrixN import MatrixNArray

        mats = MatrixNArray.lookAts(looks, ups, axis=axis)
        return mats.asQuaternionArray()

    def angles(self, other):
        """ Return the minimal angles between two quaternion rotations

        Parameters
        ----------
        other: Quaternion, QuaternionArray
            The other quaterions to compare to

        Returns
        -------
        np.ndarray:
            The calculated angles
        """
        other = arrayCompat(other)
        return 2 * np.acos(np.einsum("...ij, ...ij -> ...i", self, other))

    def slerp(self, other, tVal):
        """ Perform item-wise spherical linear interpolation at the given sample points

        Parameters
        ----------
        other: Quaterion, QuaternionArray
            The other quaternions to slerp between
        tVal: float
            The percentages to compute for the slerp. For instance .25 would
            calculate the slerp at 25% all pairs

        Returns
        -------
        QuaternnionArray:
            A quaternion array of interpolands
        """
        other = arrayCompat(other)
        cosHalfAngle = np.einsum("...ij, ...ij -> ...i", self, other)

        # Handle floating point errors
        cosHalfAngle[abs(cosHalfAngle) >= 1.0] = 1.0

        # Calculate the sin values
        halfAngle = np.acos(cosHalfAngle)
        sinHalfAngle = np.sqrt(1.0 - cosHalfAngle * cosHalfAngle)

        ratioA = np.sin((1 - tVal) * halfAngle) / sinHalfAngle
        ratioB = np.sin(tVal * halfAngle) / sinHalfAngle
        return (self * ratioA) + (other * ratioB)
