import { TestBed } from '@angular/core/testing';
import { Publicacion } from './publicacion';

describe('Publicacion', () => {
  let service: Publicacion;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Publicacion);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
