import unittest
import casadi as ca
import numpy as np
from hilo_mpc import Model, SMPC, GP


class TestIO(unittest.TestCase):
    def setUp(self):
        plant = Model(plot_backend='matplotlib')

        states = plant.set_dynamical_states(['px'])
        inputs = plant.set_inputs(['a'])
        # parameter = plant.set_parameters(['p'])

        # Unwrap states
        px = states[0]

        # Unwrap states
        a = inputs[0]

        # dpx = parameter*a
        dpx = a

        plant.set_dynamical_equations([dpx])

        # Initial conditions
        x0 = [15]

        # Create plant and run simulation
        dt = 1
        plant.setup(dt=dt)
        plant.set_initial_conditions(x0=x0)
        model = plant.copy(setup=False)
        model.discretize('erk', order=1, inplace=True)
        model.setup(dt=dt)
        model.set_initial_conditions(x0=x0)
        self.model = model

        # Setup GP
        gp = GP(['px'], 'z', solver='ipopt')
        X_train = np.array([[0., .5, 1. / np.sqrt(2.), np.sqrt(3.) / 2., 1., 0.]])
        y_train = np.array([[0., np.pi / 6., np.pi / 4., np.pi / 3., np.pi / 2., np.pi]])
        gp.set_training_data(X_train, y_train)
        gp.setup()
        gp.fit_model()
        self.gp = gp
        # Matrix
        self.B = np.array([[1]])
        self.x0 = x0

    def test_box_constraints(self):
        smpc = SMPC(self.model, self.gp, self.B)
        smpc.set_box_constraints(x_lb=[10])

    def test_box_constraints_1(self):
        smpc = SMPC(self.model, self.gp, self.B)
        self.assertRaises(TypeError, smpc.set_box_chance_constraints, x_lb=[10], x_lb_p=2)

    def test_setup(self):
        smpc = SMPC(self.model, self.gp, self.B)
        smpc.horizon = 10
        smpc.quad_stage_cost.add_states(names='mu_px', ref=1, weights=10)
        smpc.set_box_chance_constraints(x_lb=[10], x_lb_p=1)
        smpc.setup(options={'chance_constraints': 'prs'})

    def test_one_iter(self):
        smpc = SMPC(self.model, self.gp, self.B)
        smpc.horizon = 10
        smpc.quad_stage_cost.add_states(names='mu_px', ref=1, weights=10)
        smpc.set_box_chance_constraints(x_lb=[10], x_lb_p=1)
        smpc.setup(options={'chance_constraints': 'prs'})
        smpc.optimize(x0=self.x0, cov_x0=[0], Kgain=0)

    def test_not_passing_k0(self):
        smpc = SMPC(self.model, self.gp, self.B)
        smpc.horizon = 10
        smpc.quad_stage_cost.add_states(names='mu_px', ref=1, weights=10)
        smpc.set_box_chance_constraints(x_lb=[10], x_lb_p=1)
        smpc.setup(options={'chance_constraints': 'prs'})
        self.assertRaises(ValueError, smpc.optimize, x0=self.x0, Kgain=0)

    def test_plot(self):
        smpc = SMPC(self.model, self.gp, self.B)
        smpc.horizon = 10
        smpc.quad_stage_cost.add_states(names='mu_px', ref=1, weights=10)
        smpc.quad_terminal_cost.add_states(names='mu_px', ref=1, weights=10)
        smpc.set_box_chance_constraints(x_lb=[0], x_lb_p=1)
        smpc.setup(options={'chance_constraints': 'prs'})
        smpc.optimize(x0=self.x0, cov_x0=[0], Kgain=0)
        smpc.plot_prediction()


class TestMIMOSystem(unittest.TestCase):
    def setUp(self):
        plant = Model(plot_backend='matplotlib')

        states = plant.set_dynamical_states(['px', 'py'])
        inputs = plant.set_inputs(['ax', 'ay'])
        # parameter = plant.set_parameters(['p'])

        # unwrap states
        px = states[0]
        py = states[1]

        # unwrap states
        a1 = inputs[0]
        a2 = inputs[1]

        # dpx = parameter*a
        dpx = a1
        dpy = a2 + px

        plant.set_dynamical_equations([dpx, dpy])

        # initial conditions
        x0 = [15, 10]

        # create plant and run simulation
        dt = 1
        plant.setup(dt=dt)
        plant.set_initial_conditions(x0=x0)
        model = plant.copy(setup=False)
        model.discretize('erk', order=1, inplace=True)
        model.setup(dt=dt)
        model.set_initial_conditions(x0=x0)
        self.model = model

        # setup gp
        gp = GP(['px'], 'z', solver='ipopt')
        x_train = np.array([[0., .5, 1. / np.sqrt(2.), np.sqrt(3.) / 2., 1., 0.]])
        y_train = np.array([[0., np.pi / 6., np.pi / 4., np.pi / 3., np.pi / 2., np.pi]])
        gp.set_training_data(x_train, y_train)
        gp.setup()
        gp.fit_model()
        self.gp = gp
        # matrix
        self.B = np.array([[1, 0]]).T
        self.x0 = x0

    def test_simple_mimo(self):
        smpc = SMPC(self.model, self.gp, self.B)
        smpc.horizon = 10
        smpc.quad_stage_cost.add_states(names=['mu_px', 'mu_py'], ref=[1, 1], weights=[10,10])
        smpc.quad_terminal_cost.add_states(names=['mu_px', 'mu_py'], ref=[1, 1], weights=[10,10])
        smpc.set_box_chance_constraints(x_lb=[0, 0], x_lb_p=[1, 1])
        smpc.setup(options={'chance_constraints': 'prs'})
        cov_x0 = np.array([[0, 0], [0, 0]])
        Kgain = np.array([[0, 0], [0, 0]])
        smpc.optimize(x0=self.x0, cov_x0=cov_x0, Kgain=Kgain)
        smpc.plot_prediction()


if __name__ == '__main__':
    unittest.main()
