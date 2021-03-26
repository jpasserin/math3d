import numpy as np
from .utils import arrayCompat, toType, asarray


class VectorN(np.ndarray):
    def __new__(cls, input_array=None):
        if input_array is None:
            ary = np.zeros(cls.N)
        else:
            ary = np.asarray(input_array, dtype=float)
        if ary.size != cls.N:
            raise ValueError(
                "Initializer for Vector{0} must be of length {0}".format(cls.N)
            )
        return ary.view(cls)

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
            if shape[0] == cls.N:
                return cls
        elif len(shape) == 2:
            # This could happen with fancy indexing
            if shape[-1] == cls.N:
                return cls.arrayType

        return np.ndarray

    def __getitem__(self, idx):
        ret = super(VectorN, self).__getitem__(idx)
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

    def lengthSquared(self):
        """ Return the squared length of each vector

        Returns
        -------
        np.ndarray:
            The squared lengths of the vectors
        """
        return (self * self).sum()

    def length(self):
        """ Return the length of each vector

        Returns
        -------
        np.ndarray:
            The lengths of the vectors
        """
        return np.sqrt(self.lengthSquared())

    @classmethod
    def ones(cls):
        """ Alternate constructor to build a vector of all ones """
        return cls(np.ones(cls.N))

    @classmethod
    def full(cls, value):
        """ Alternate constructor to build a vector of a given value """
        return cls(np.full(cls.N, value))

    def asVectorSize(self, n, pad=1.0):
        """ Return a vector of a given size based on the current vector.
        Discard the ending items if the size is smaller
        Pad up if the size is bigger, filled with the pad value

        If the requested size is smaller, keep the upper left square of the matrix
        If the size is bigger, the new entries will the same as the identity matrix

        Parameters
        ----------
        n: int
            The new size of the vector
        pad: float
            The padding value for expanding the vector

        """
        if n == self.N:
            return self.copy()
        typ = VECTOR_BY_SIZE[n]
        ret = typ.full(pad)
        n = min(n, self.N)
        ret[:n] = self[:n]
        return ret

    def cross(self, other):
        """ Take Cross product with another vector

        Parameters
        ----------
        other: VectorN
            The value to cross with

        Returns
        -------
        VectorN:
            The result of the cross product
        """
        return np.cross(self, other)

    def __mul__(self, other):
        other = asarray(other)
        if isinstance(other, VectorN):
            if self.N != other.N:
                raise TypeError(
                    "Cannot compute the dot of vectors with different sizes"
                )
            return np.dot(self, other)
        elif isinstance(other, VectorNArray):
            if self.N != other.N:
                raise TypeError(
                    "Cannot compute the dot of vectors with different sizes"
                )
            return np.einsum("ij, ij -> i", self.asArray(), other)

        from .matrixN import MatrixN, MatrixNArray

        if isinstance(other, MatrixN):
            if other.N < self.N:
                raise TypeError("Can't mutiply a vector by a smaller matrix")
            exp = self.asVectorSize(other.N)
            ret = np.dot(self, other)
            return ret.asVectorSize(self.N)
        elif isinstance(other, MatrixNArray):
            if other.N < self.N:
                raise TypeError("Can't mutiply a vector by a smaller matrix")
            exp = self.asVectorSize(other.N)
            ret = np.einsum("ij, ijk -> ik", exp.asArray(), other)
            return ret.asVectorSize(self.N)

        from .quaternion import Quaternion, QuaternionArray

        if isinstance(other, Quaternion):
            exp = self.asVectorSize(3)
            ret = QuaternionArray.vectorquatproduct(exp.asArray(), other.asArray())
            return ret[0].asVectorSize(self.N)

        elif isinstance(other, QuaternionArray):
            exp = self.asVectorSize(3)
            ret = QuaternionArray.vectorquatproduct(exp.asArray(), other)
            return ret.asVectorSize(self.N)

        return super(VectorN, self).__mul__(other)

    @classmethod
    def planeNormal(cls, center, pos1, pos2, normalize=False):
        """ Convenience constructor to build a plane normal based off 3 points
        Simply cross the "spoke" vectors from the centers
            (pos1-center) x (pos2-center)

        The cross product only works in 3d, therefore all calculations will be done
        at that length

        Parameters
        ----------
        center: Vector3
            The "central" point
        pos1: Vector3
            The first axis point
        pos2: vector3
            The second axis point
        """
        center, pos1, pos2 = arrayCompat(center, pos1, pos2)
        ret = VectorNArray.planeNormals(center, pos1, pos2, normalize=normalize)
        return ret[0]

    def distance(self, other):
        """ Get the per-point distances to another set of vectors

        Parameters
        ----------
        other: VectorN, VectorNArray
            The Point or Points to get distances to

        Returns
        -------
        np.ndarray
            The computed distances
        """
        if isinstance(other, VectorNArray):
            return (self.asArray() - other).length()
        return (self - other).length()

    def lerp(self, other, percent):
        sa = self
        if isinstance(other, VectorNArray):
            sa = self.asArray()
        return ((other - sa) * percent) + sa


class VectorNArray(np.ndarray):
    def __new__(cls, input_array):
        ary = np.asarray(input_array, dtype=float)
        ary = ary.reshape((-1, cls.N))
        return ary.view(cls)

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
            if shape[1] == cls.N:
                return cls
            return np.ndarray
        elif len(shape) == 1:
            if shape[0] == cls.N:
                return cls.itemType
        return np.ndarray

    def __getitem__(self, idx):
        ret = super(VectorNArray, self).__getitem__(idx)
        typ = self.getReturnType(ret.shape)
        if typ is None:
            return ret
        return ret.view(typ)

    def lengthSquared(self):
        """ Return the squared length of each vector

        Returns
        -------
        np.ndarray:
            The squared lengths of the vectors
        """
        return np.einsum("...ij,...ij->...i", self, self)

    def length(self):
        """ Return the length of each vector

        Returns
        -------
        np.ndarray:
            The lengths of the vectors
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
    def ones(cls, length):
        """ Alternate constructor to build a vector of all ones

        Parameters
        ----------
        length: int
            The number of matrices to build
        """
        return cls(np.ones((length, cls.N)))

    @classmethod
    def full(cls, length, value):
        """ Alternate constructor to build a vector of a given value

        Parameters
        ----------
        length: int
            The number of matrices to build
        value: float
            The value to fill the vectors with
        """
        return cls(np.full((length, cls.N), value))

    def asVectorSize(self, n, pad=1.0):
        """ Return a vector of a given size based on the current vector.
        Discard the ending items if the size is smaller
        Pad up if the size is bigger, filled with the pad value

        If the requested size is smaller, keep the upper left square of the matrix
        If the size is bigger, the new entries will the same as the identity matrix

        Parameters
        ----------
        n: int
            The new size of the vector
        pad: float
            The padding value for expanding the vector

        """
        if n == self.N:
            return self.copy()
        typ = VECTOR_ARRAY_BY_SIZE[n]
        ret = typ.full(len(self), pad)
        n = min(n, self.N)
        ret[:, :n] = self[:, :n]
        return ret

    def append(self, v):
        """ Append an item to the end of this array

        Parameters
        ----------
        value: iterable
            An iterable to be appended as-is to the end of this array
        """
        self.resize((len(self) + 1, self.N))
        self[-1] = v

    def extend(self, v):
        """ Extend this array with the given items

        Parameters
        ----------
        value: iterable
            An iterable to be added to the end of this array
        """
        self.resize((len(self) + len(v), self.N))
        self[-len(v) :] = v

    def cross(self, other):
        """ Take Cross product with another array of vector

        Parameters
        ----------
        other: VectorNArray
            The values to cross with

        Returns
        -------
        VectorNArray:
            The result of the per-row cross product
        """
        other = arrayCompat(other)
        return np.cross(self, other)

    def __mul__(self, other):
        other = asarray(other)
        if isinstance(other, VectorNArray):
            if other.N != self.N:
                raise TypeError("Can't dot vectors of different length")
            return np.einsum("...ij,...ij->...i", self, other)
        elif isinstance(other, VectorN):
            if other.N != self.N:
                raise TypeError("Can't dot vectors of different length")
            return np.dot(self, other)

        from .matrixN import MatrixN, MatrixNArray

        if isinstance(other, MatrixN):
            if other.N < self.N:
                raise TypeError("Can't mutiply a vector by a smaller matrix")
            exp = self.asVectorSize(other.N)
            ret = np.dot(exp, other)
            return ret.asVectorSize(self.N)
        elif isinstance(other, MatrixNArray):
            if other.N < self.N:
                raise TypeError("Can't mutiply a vector by a smaller matrix")
            exp = self.asVectorSize(other.N)
            ret = np.einsum("...ij, ...ijk -> ...ik", exp, other)
            return ret.asVectorSize(self.N)

        from .quaternion import Quaternion, QuaternionArray

        if isinstance(other, Quaternion):
            exp = self.asVectorSize(3)
            ret = QuaternionArray.vectorquatproduct(exp, other.asArray())
            return ret.asVectorSize(self.N)

        elif isinstance(other, QuaternionArray):
            exp = self.asVectorSize(3)
            ret = QuaternionArray.vectorquatproduct(exp, other)
            return ret.asVectorSize(self.N)

        return super(VectorNArray, self).__mul__(other)

    def angle(self, other):
        """ Get the angle between pairs of vectors

        Parameters
        ----------
        other: VectorNArray
            The array of vectors to get the angles between

        Returns
        -------
        np.ndarray:
            The angles between the paired vectors in radians
        """
        other = arrayCompat(other)
        typ = type(self)
        if not isinstance(other, typ):
            other = other.view(typ)

        return np.acos(self.normal() * other.normal())

    @classmethod
    def planeNormals(cls, centers, pos1, pos2, normalize=False):
        """ Convenience constructor to build plane normals based off 3 sets of points
        Simply cross the "spoke" vectors from the centers
            (pos1-centers) x (pos2-centers)

        The cross product only works in 3d, therefore all calculations will be done
        at that length

        Parameters
        ----------
        centers: Vector3Array
            The "central" set of points
        pos1: Vector3Array
            The array of first axis points
        pos2: vector3Array
            The array of second axis points
        """
        centers, pos1, pos2 = arrayCompat(centers, pos1, pos2)
        centers, pos1, pos2 = toType(VECTOR_ARRAY_BY_SIZE[3], centers, pos1, pos2)

        vec1 = (pos1 - centers).normal()
        vec2 = (pos2 - centers).normal()

        ret = np.cross(vec1, vec2)
        if normalize:
            ret.normalize()
        return ret

    def adjacentLengths(self):
        """ Return the distance between each adjacent pair if vertices

        Returns
        -------
        np.ndarray
            The length of each adjacent pair if vertices
        """
        if len(self) < 2:
            raise ValueError("There must be at least 2 vectors to get adjacent lengths")
        return (self[1:] - self[:-1]).length()

    def distances(self, other):
        """ Get the per-point distances to another set of vectors

        Parameters
        ----------
        other: VectorN, VectorNArray
            The Point or Point to get distances to

        Returns
        -------
        np.ndarray
            The computed distances
        """
        if other.ndim == 1:
            other = other[None, ...]
        return (self - other).length()

    def lerp(self, other, percent):
        """ Linearly interpolate between two sets of vectors

        Parameters
        ----------
        other: VectorNArray, VectorN, np.ndarray, list
            The other set of vectors to interpolate with
        percent: np.ndarray, float
            The percentage to interpolate. If it's iterable, the list must be
            exactly as long as self and other

        Returns
        -------
        VectorNArray:
            The new points some percentage of the way to the other points
        """
        other = arrayCompat(other)
        percent = arrayCompat(percent, nDim=1)
        return ((other - self) * percent[..., None]) + self

    def parallelTransport(self, upv, inverse=False):
        """ Take a normal and transport it along these ordered points.
        When 3 adjacent points aren't in a straight line, rotate the normal
        by the angle of those points

        Parameters
        ----------
        upv: Vector3
            The single starting up-vector
        inverse: bool
            Whether to invert the rotation for flipping

        Returns
        -------
        VectorNArray:
            An array of normals per point
        """
        from .quaternion import QuaternionArray

        adjVecs = self[1:] - self[:-1]
        # get the rotation and axis for all points except the first and last
        binorms = adjVecs[1:].cross(adjVecs[:-1])
        angles = adjVecs[1:].angle(adjVecs[:-1])
        if inverse:
            angles *= -1
        quats = QuaternionArray.axisAngle(binorms, angles)

        # The first upvector is the given value
        out = VECTOR_ARRAY_BY_SIZE[3].zeros(len(self))
        out[0] = upv
        for i in range(len(self) - 1):
            out[i + 1] = out[i] * quats[i]

        # The last upvector is a repeat of the previous one
        out[-1] = out[-2]
        return out


# Register the default sizes of array dynamically
VECTOR_BY_SIZE = {}
VECTOR_ARRAY_BY_SIZE = {}
glo = globals()
for n in [2, 3, 4]:
    name = "Vector{0}".format(n)
    aname = "Vector{0}Array".format(n)
    v = type(name, (VectorN,), {"N": n})
    va = type(aname, (VectorNArray,), {"N": n})
    v.arrayType = va
    va.itemType = v
    glo[name] = v
    glo[aname] = va
    VECTOR_BY_SIZE[n] = v
    VECTOR_ARRAY_BY_SIZE[n] = va
