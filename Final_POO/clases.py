from abc import ABC, abstractmethod

class Vehiculo(ABC):
    def __init__(self, marca, modelo, anio, kilometraje, tipoCombustible, estado):
        self.__marca = marca
        self.__modelo = modelo
        self.__anio = anio
        self.__kilometraje = kilometraje
        self.__tipoCombustible = tipoCombustible
        self.__estado = estado

    def mostrasVehiculo(self):
        return (f"Vehiculo marca: {self.__marca}, Modelo: {self.__modelo}, Año: {self.__anio}, "
                f"Kilometraje: {self.__kilometraje}, Tipo de combustible: {self.__tipoCombustible}"
                f"Estado: {self.__estado}")




class Auto(Vehiculo):
    pass



class Moto(Vehiculo):
    pass