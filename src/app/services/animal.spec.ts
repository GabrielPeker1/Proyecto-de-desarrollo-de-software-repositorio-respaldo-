import { TestBed } from '@angular/core/testing';
import { Animal } from './animal';

describe('Animal', () => {
  let service: Animal;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Animal);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
