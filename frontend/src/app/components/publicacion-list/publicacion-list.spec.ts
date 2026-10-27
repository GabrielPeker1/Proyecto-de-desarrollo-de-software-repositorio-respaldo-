import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PublicacionList } from './publicacion-list';

describe('PublicacionList', () => {
  let component: PublicacionList;
  let fixture: ComponentFixture<PublicacionList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PublicacionList],
    }).compileComponents();

    fixture = TestBed.createComponent(PublicacionList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
