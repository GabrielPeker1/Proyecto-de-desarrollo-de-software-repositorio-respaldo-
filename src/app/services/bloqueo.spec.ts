import { TestBed } from '@angular/core/testing';
import { Bloqueo } from './bloqueo';

describe('Bloqueo', () => {
  let service: Bloqueo;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Bloqueo);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
