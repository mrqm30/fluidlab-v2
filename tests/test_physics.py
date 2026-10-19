"""Pruebas numéricas y físicas, usando solo unittest."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physics import calculate, PhysicsError

BASE={'rho':998.2,'viscosity_kind':'dynamic','viscosity_value':.001002}

def run(**kwargs):
    return calculate({**BASE,**kwargs})

def value(result, name):
    return next(m['value'] for m in result['metrics'] if m['label']==name)

class PhysicsTests(unittest.TestCase):
    def test_film_profile_mean_and_boundary_conditions(self):
        d=run(module='film',delta=.0004,width=.25,length=1,beta=25)
        vmax=value(d,'Velocidad máxima');vmean=value(d,'Velocidad media')
        self.assertAlmostEqual(vmax/vmean,1.5)
        self.assertAlmostEqual(d['profile']['points'][-1][1],0,places=8)
        self.assertEqual(d['stress']['points'][0][1],0)
        self.assertAlmostEqual(value(d,'Caudal volumétrico'),vmean*.25*.0004)
        self.assertAlmostEqual(value(d,'Fuerza viscosa'),value(d,'Esfuerzo en pared')*.25*1)

    def test_pipe_hagen_poiseuille_and_wall(self):
        d=run(module='pipe',radius=.004,length=2,dp=20,orientation='horizontal')
        mean=value(d,'Velocidad media');maximum=value(d,'Velocidad máxima')
        self.assertAlmostEqual(maximum,2*mean)
        self.assertAlmostEqual(value(d,'Caudal volumétrico'),math.pi*.004**2*mean)
        self.assertAlmostEqual(value(d,'Esfuerzo en pared'),20*.004/(2*2))
        self.assertAlmostEqual(d['profile']['points'][-1][1],0)
        self.assertAlmostEqual(value(d,'ΔP viscoso equivalente'),20)

    def test_uphill_force(self):
        with self.assertRaises(PhysicsError):
            run(module='pipe',radius=.01,length=1,dp=1,orientation='up')
        d=run(module='pipe',radius=.01,length=1,dp=20000,orientation='up')
        self.assertGreater(value(d,'Caudal volumétrico'),0)

    def test_parallel_plates(self):
        d=run(module='plates',half_gap=.001,width=.12,length=1.2,dp=30)
        maxvel=value(d,'Velocidad máxima');mean=value(d,'Velocidad media')
        self.assertAlmostEqual(maxvel/mean,1.5)
        self.assertAlmostEqual(value(d,'Caudal volumétrico'),mean*2*.001*.12)
        self.assertAlmostEqual(d['profile']['points'][0][1],0)
        self.assertAlmostEqual(d['profile']['points'][-1][1],0)
        self.assertAlmostEqual(d['stress']['points'][0][1],-d['stress']['points'][-1][1])

    def test_viscosity_dynamic_and_kinematic(self):
        d=run(module='viscosity',speed=.4,gap=.002,area=.3)
        self.assertAlmostEqual(value(d,'Tasa de corte γ̇'),200)
        self.assertAlmostEqual(value(d,'Esfuerzo cortante τ'),.001002*200)
        self.assertAlmostEqual(value(d,'Fuerza tangencial F'),.001002*200*.3)
        nu=.001002/998.2
        dk=calculate({'module':'viscosity','rho':998.2,'viscosity_kind':'kinematic','viscosity_value':nu,'speed':.4,'gap':.002,'area':.3})
        self.assertAlmostEqual(value(dk,'Esfuerzo cortante τ'),value(d,'Esfuerzo cortante τ'))

    def test_annular_integration(self):
        d=run(module='annulus',inner_radius=.004,outer_radius=.01,length=2,dp=60)
        pts=d['profile']['points']
        self.assertAlmostEqual(pts[0][1],0,places=8)
        self.assertAlmostEqual(pts[-1][1],0,places=8)
        self.assertGreater(value(d,'Velocidad máxima'),value(d,'Velocidad media'))
        # Numeric integration Q = ∫ 2πr v(r) dr, x is mm.
        q=0
        for (r0,v0),(r1,v1) in zip(pts,pts[1:]):
            q+=math.pi*(r1-r0)/1000*((r0/1000)*v0+(r1/1000)*v1)
        self.assertAlmostEqual(q/value(d,'Caudal volumétrico'),1,places=4)

    def test_validation(self):
        with self.assertRaises(PhysicsError):
            run(module='film',delta=-1,width=.2,length=1,beta=10)
        with self.assertRaises(PhysicsError):
            run(module='annulus',inner_radius=.01,outer_radius=.01,length=1,dp=12)
        with self.assertRaises(PhysicsError):
            calculate({**BASE,'module':'pipe','radius':.01,'length':1,'dp':float('nan')})
        with self.assertRaises(PhysicsError):
            calculate({**BASE,'viscosity_value':0,'module':'pipe','radius':.01,'length':1,'dp':100})
        with self.assertRaises(PhysicsError):
            calculate({**BASE,'module':'not-real'})

if __name__=='__main__':unittest.main()

class ExtensionTests(unittest.TestCase):
    def test_gas_sutherland_density_and_temperature(self):
        common=dict(module='gas',gas_name='air',pressure=101325,speed=0.5,gap=.002,area=.1)
        a=calculate({**common,'temperature_C':20})
        b=calculate({**common,'temperature_C':90})
        self.assertAlmostEqual(value(a,'Densidad del gas ρ'),1.204118,places=4)
        self.assertAlmostEqual(value(a,'Viscosidad dinámica μ'),1.813e-5,delta=6e-8)
        self.assertGreater(value(b,'Viscosidad dinámica μ'),value(a,'Viscosidad dinámica μ'))
        self.assertLess(value(b,'Densidad del gas ρ'),value(a,'Densidad del gas ρ'))
        self.assertAlmostEqual(value(a,'Esfuerzo cortante τ'),value(a,'Viscosidad dinámica μ')*250)

    def test_gas_pressure_affects_nu_not_mu(self):
        d=dict(module='gas',gas_name='co2',temperature_C=30,speed=.1,gap=.002,area=.1)
        lo=calculate({**d,'pressure':100000})
        hi=calculate({**d,'pressure':200000})
        self.assertAlmostEqual(value(lo,'Viscosidad dinámica μ'),value(hi,'Viscosidad dinámica μ'))
        self.assertAlmostEqual(value(hi,'Densidad del gas ρ'),2*value(lo,'Densidad del gas ρ'))
        self.assertAlmostEqual(value(lo,'Viscosidad cinemática ν'),2*value(hi,'Viscosidad cinemática ν'))

    def test_metal_reference_and_phase(self):
        d=dict(module='metal',metal_name='gallium',temperature_C=35,reference_C=35,
               reference_mu=.0019,reference_rho=6095,activation_energy=0,
               speed=.3,gap=.003,area=.1)
        r=calculate(d)
        self.assertAlmostEqual(value(r,'Viscosidad dinámica μ'),.0019)
        self.assertAlmostEqual(value(r,'Esfuerzo cortante τ'),.19)
        with self.assertRaises(PhysicsError):
            calculate({**d,'temperature_C':25})
        with self.assertRaises(PhysicsError):
            calculate({**d,'temperature_C':50})  # no thermal calibration

    def test_metal_temperature_requires_activation(self):
        d=dict(module='metal',metal_name='sodium',temperature_C=160,reference_C=120,
               reference_mu=.00065,reference_rho=927,activation_energy=6500,
               speed=.1,gap=.002,area=.1)
        r=calculate(d)
        self.assertLess(value(r,'Viscosidad dinámica μ'),.00065)
        self.assertAlmostEqual(r['profile']['points'][0][0],120.0,delta=.01)

    def test_mixture_liquid_endpoints_and_density(self):
        d=dict(module='mixture',mix_type='liquid',mu1=.001,mu2=.1,rho1=1000,rho2=800)
        r=calculate({**d,'fraction':.25})
        self.assertAlmostEqual(value(r,'Viscosidad de mezcla μ'),.001**.25*.1**.75)
        self.assertAlmostEqual(value(r,'Densidad de mezcla ρ'),850)
        self.assertAlmostEqual(value(calculate({**d,'fraction':0}),'Viscosidad de mezcla μ'),.1)
        self.assertAlmostEqual(value(calculate({**d,'fraction':1}),'Viscosidad de mezcla μ'),.001)

    def test_wilke_endpoints_and_symmetry(self):
        d=dict(module='mixture',mix_type='gas',gas_a='nitrogen',gas_b='oxygen',
               temperature_C=30,pressure=101325)
        one=calculate({**d,'fraction':1})
        zero=calculate({**d,'fraction':0})
        self.assertGreater(value(zero,'Viscosidad de mezcla μ'),value(one,'Viscosidad de mezcla μ'))
        mix=calculate({**d,'fraction':.3})
        swapped=calculate({**d,'gas_a':'oxygen','gas_b':'nitrogen','fraction':.7})
        self.assertAlmostEqual(value(mix,'Viscosidad de mezcla μ'),value(swapped,'Viscosidad de mezcla μ'))
        self.assertAlmostEqual(value(mix,'Densidad de mezcla ρ'),value(swapped,'Densidad de mezcla ρ'))

    def test_couette_matches_pure_shear(self):
        d=run(module='couette',gap=.002,speed_lower=0,speed_upper=.4,width=.3,length=2,dp=0)
        self.assertAlmostEqual(value(d,'Velocidad media v̄'),.2)
        self.assertAlmostEqual(value(d,'Caudal neto Q'),.2*.002*.3)
        self.assertAlmostEqual(value(d,'Esfuerzo placa inferior'),.001002*.4/.002)
        self.assertAlmostEqual(value(d,'Esfuerzo placa superior'),.001002*.4/.002)
        self.assertAlmostEqual(value(d,'Fuerza sobre placa inferior'),-value(d,'Fuerza sobre placa superior'))
        self.assertAlmostEqual(d['profile']['points'][0][1],0)
        self.assertAlmostEqual(d['profile']['points'][-1][1],.4)

    def test_couette_matches_plane_poiseuille(self):
        d=run(module='couette',gap=.002,speed_lower=0,speed_upper=0,width=.3,length=2,dp=50)
        mean=50*.002**2/(12*.001002*2)
        self.assertAlmostEqual(value(d,'Velocidad media v̄'),mean)
        self.assertAlmostEqual(value(d,'Caudal neto Q'),mean*.002*.3)
        self.assertAlmostEqual(d['profile']['points'][0][1],0)
        self.assertAlmostEqual(d['profile']['points'][-1][1],0)
        self.assertAlmostEqual(value(d,'Esfuerzo placa inferior'),-value(d,'Esfuerzo placa superior'))

    def test_couette_two_moving_walls_and_opposing_pressure(self):
        d=run(module='couette',gap=.003,speed_lower=-.2,speed_upper=.4,width=.1,length=1,dp=-10)
        self.assertAlmostEqual(d['profile']['points'][0][1],-.2)
        self.assertAlmostEqual(d['profile']['points'][-1][1],.4)
        self.assertAlmostEqual(value(d,'Velocidad media v̄'),.1-10*.003**2/(12*.001002))

    def test_extension_validation(self):
        with self.assertRaises(PhysicsError):
            calculate(dict(module='gas',gas_name='water',temperature_C=20,pressure=101325,speed=.2,gap=.01,area=.2))
        with self.assertRaises(PhysicsError):
            calculate(dict(module='mixture',mix_type='liquid',fraction=1.1,mu1=.1,mu2=.2,rho1=1000,rho2=1100))
        with self.assertRaises(PhysicsError):
            run(module='couette',gap=0,speed_lower=0,speed_upper=.1,width=.1,length=1,dp=0)
