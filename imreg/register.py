""" A top level registration module """

import numpy as np


class Coordinates(object):
    """
    Container for grid coordinates.

    Attributes
    ----------
    domain : nd-array
        Domain of the coordinate system.
    tensor : nd-array
        Grid coordinates.
    homogenous : nd-array
        `Homogenous` coordinate system representation of grid coordinates.
    """

    def __init__(self, domain, spacing=None):

        self.domain = domain
        self.tensor = np.mgrid[0.:domain[1], 0.:domain[3]]

        self.homogenous = np.zeros((3, self.tensor[0].size))
        self.homogenous[0] = self.tensor[1].flatten()
        self.homogenous[1] = self.tensor[0].flatten()
        self.homogenous[2] = 1.0


class RegisterData(object):
    """
    Container for registration data.

    Attributes
    ----------
    data : nd-array
        The image registration image values.
    coords : nd-array, optional
        The grid coordinates.
    """

    def __init__(self, data, coords=None, features=None, spacing=1.0):

        self.data = data.astype(np.double)

        if not coords:
            self.coords = Coordinates(
                [0, data.shape[0], 0, data.shape[1]],
                spacing=spacing
                )
        else:
            self.coords = coords


class optStep():
    """
    A container class for optimization steps.

    Attributes
    ----------
    error: float
        Normalised fitting error.
    p: nd-array
        Model parameters.
    deltaP: nd-array
        Model parameter update vector.
    decreasing: boolean.
        State of the error function at this point.
    """

    def __init__(self, error=None, p=None, deltaP=None, decreasing=None):
        self.error = error
        self.p = p
        self.deltaP = deltaP
        self.decreasing = decreasing


class Register(object):
    """
    A registration class for estimating the deformation model parameters that
    best solve:

    | :math:`f( W(I;p), T )`
    |
    | where:
    |    :math:`f`     : is a similarity metric.
    |    :math:`W(x;p)`: is a deformation model (defined by the parameter set p).
    |    :math:`I`     : is an input image (to be deformed).
    |    :math:`T`     : is a template (which is a deformed version of the input).

    Notes:
    ------

    Solved using a modified gradient descent algorithm.

    .. [0] Levernberg-Marquardt algorithm,
           http://en.wikipedia.org/wiki/Levenberg-Marquardt_algorithm

    Attributes
    ----------
    model: class
        A `deformation` model class definition.
    metric: class
        A `similarity` metric class definition.
    sampler: class
        A `sampler` class definition.
    """

    MAX_ITER = 200
    MAX_BAD = 5

    def __init__(self, model, metric, sampler):

        self.model = model
        self.metric = metric
        self.sampler = sampler

    def __deltaP(self, J, e, alpha, p=None):
        """
        Computes the parameter update.

        Parameters
        ----------
        J: nd-array
            The (dE/dP) the relationship between image differences and model
            parameters.
        e: float
            The evaluated similarity metric.
        alpha: float
            A dampening factor.
        p: nd-array or list of floats, optional

        Returns
        -------
        deltaP: nd-array
           The parameter update vector.
        """

        H = np.dot(J.T, J)

        H += np.diag(alpha * np.diagonal(H))

        return np.dot(np.linalg.inv(H), np.dot(J.T, e))

    def __dampening(self, alpha, decreasing):
        """
        Computes the adjusted dampening factor.

        Parameters
        ----------
        alpha: float
            The current dampening factor.
        decreasing: boolean
            Conditional on the decreasing error function.

        Returns
        -------
        alpha: float
           The adjusted dampening factor.
        """
        return alpha / 10. if decreasing else alpha * 10.

    def register(self, image, template, p=None, alpha=None, verbose=False):
        """
        Computes the registration between the image and template.

        Parameters
        ----------
        image: nd-array
            The floating image.
        template: nd-array
            The target image.
        p: list (or nd-array), optional.
            First guess at fitting parameters.
        alpha: float
            The dampening factor.
        verbose: boolean
            A debug flag for text status updates.

        Returns
        -------
        p: nd-array.
            Model parameters.
        warp: nd-array.
            (inverse) Warp field estimate.
        warpedImage: nd-array
            The re-sampled image.
        error: float
            Fitting error.
        """

        # Initialize the models, metric and sampler.
        model = self.model(image.coords)
        sampler = self.sampler(image.coords)
        metric = self.metric()

        p = model.identity if p is None else p
        deltaP = np.zeros_like(p)

        # Dampening factor.
        alpha = alpha if alpha is not None else 1e-4

        # Variables used to implement a back-tracking algorithm.
        search = []
        badSteps = 0
        bestStep = None

        for itteration in range(0, self.MAX_ITER):

            # Compute the inverse "warp" field.
            warp = model.warp(p)

            # Sample the image using the inverse warp, the reshape is a
            # view.
            warpedImage = sampler.f(image.data, warp)
            warpedImage.shape = image.data.shape

            # Evaluate the error metric.
            e = metric.error(warpedImage, template.data)

            # Cache the optimization step.
            searchStep = optStep(
               error=np.abs(e).sum() / np.prod(image.data.shape),
               p=p.copy(),
               deltaP=deltaP.copy(),
               decreasing=True
               )

            # Update the current best step.
            bestStep = searchStep if bestStep is None else bestStep

            if verbose:
                print ('{0}\n'
                       'iteration  : {1} \n'
                       'parameters : {2} \n'
                       'error      : {3} \n'
                       '{0}'
                      ).format(
                            '='*80,
                            itteration,
                            ' '.join( '{0:3.2f}'.format(param) for param in searchStep.p),
                            searchStep.error
                            )

            # Append the search step to the search.
            search.append(searchStep)

            if len(search) > 1:

                searchStep.decreasing = (searchStep.error < bestStep.error)

                alpha = self.__dampening(
                    alpha,
                    searchStep.decreasing
                    )

                if searchStep.decreasing:
                    bestStep = searchStep
                else:
                    badSteps += 1
                    if badSteps > self.MAX_BAD:
                        if verbose:
                            print ('Optimization break, maximum number '
                                   'of bad iterations exceeded.')
                        break

                    # Restore the parameters from the previous best iteration.
                    p = bestStep.p.copy()

            # Computes the derivative of the error with respect to model
            # parameters.

            J = metric.jacobian(model, warpedImage, p)

            # Compute the parameter update vector.
            deltaP = self.__deltaP(J, e, alpha, p)

            # Evaluate stopping condition:
            if np.dot(deltaP.T, deltaP) < 1e-4:
                break

            # Update the estimated parameters.
            p += deltaP

        return bestStep, warpedImage, search