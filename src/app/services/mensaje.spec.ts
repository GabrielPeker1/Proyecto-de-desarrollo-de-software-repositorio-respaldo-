import { TestBed } from '@angular/core/testing';
import { Mensaje } from './mensaje';

describe('Mensaje', () => {
  let service: Mensaje;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Mensaje);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
