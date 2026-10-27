import { TestBed } from '@angular/core/testing';
import { Solicitud } from './solicitud';

describe('Solicitud', () => {
  let service: Solicitud;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Solicitud);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
