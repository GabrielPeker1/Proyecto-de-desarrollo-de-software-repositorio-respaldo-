import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { BloqueoService } from './bloqueo';

describe('BloqueoService', () => {
  let service: BloqueoService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient()] });
    service = TestBed.inject(BloqueoService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
