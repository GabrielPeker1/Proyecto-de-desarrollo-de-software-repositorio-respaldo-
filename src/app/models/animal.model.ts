export class FotoAnimal {
  id_foto!: number;
  url_foto!: string;
  animal_id?: number;
}

export class Animal {
  id_animal!: number;
  nombre!: string;
  especie!: string;
  raza?: string;
  edad!: string;
  sexo?: string;
  peso?: number;
  vacunas_administradas?: string;
  castrado!: boolean;
  compatible_ninos!: boolean;
  compatible_otros_animales!: boolean;
  desparasitado!: boolean;
  tiene_microchip!: boolean;
  entrenamiento_basico!: boolean;
  fotos?: FotoAnimal[];
  fotos_urls?: string[];
}

export type AnimalCreate = Omit<Animal, 'id_animal' | 'fotos'>;